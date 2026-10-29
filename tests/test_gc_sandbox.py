"""Actual unlink faults on fresh isolated synthetic temporary volumes only."""
import copy
import hashlib
import io
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

from asc.catalog.common import uid
from asc.replication.sandbox import fixture_executor,Executor
from asc.storage.engine import StorageEngine
from asc.storage.errors import StorageError


class SimulatedCrash(BaseException):pass


@unittest.skipUnless(os.name=='posix','isolated physical executor is Linux-only; Windows execution remains locked')
class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='asc-gc-sandbox-');self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.node_id=uid()
        self.engine=StorageEngine(self.base/'private',self.node_id);self.addCleanup(lambda:self.engine.close())
        self.volume=self.engine.volumes.register(self.base/'volume',quota=1024**2,reserve=0)['volume_id']
        self.executor=fixture_executor(self.engine,self.volume)
        self.global_id=uid();self.replica_id=uid();self.data=b'synthetic isolated GC bytes\0'*128
        self.sha=hashlib.sha256(self.data).hexdigest();self.path='_asc-global/'+self.global_id+'/'+self.replica_id
        session=self.engine.initiate('job:'+uid(),self.volume,'gc-body-0001',self.path,len(self.data),self.sha)
        self.engine.upload(session['session_id'],session['principal'],self.volume,io.BytesIO(self.data),len(self.data))
        self.file=self.engine.commit(session['session_id'],session['principal'],self.volume)
        self.body=self.base/'volume'/'objects'/(self.file['file_id']+'.blob')
        self.contract={'kind':'gc','gc_job_id':uid(),'retired_replica_id':self.replica_id,'node_id':self.node_id,
            'volume_id':self.volume,'local_file_id':self.file['file_id'],'file_id':self.global_id,'logical_path':self.path,
            'size':len(self.data),'sha256':self.sha,'cluster_id':uid(),'epoch':uid(),'plan_sha256':'a'*64,
            'permit_term':4,'run_id':uid(),'permit_expires_at':int(time.time())+120}
        self.authorize=mock.Mock(side_effect=self.authority)

    def authority(self):
        return {'constraints':copy.deepcopy(self.contract),'authority':{'cluster_id':self.contract['cluster_id'],
            'epoch':self.contract['epoch'],'term':self.contract['permit_term'],'index':100,'nonce':uid()}}

    def execute(self):return self.executor.execute(self.contract,self.authorize)

    def test_default_no_capability_fresh_volume_only_and_exact_body_idempotency(self):
        with self.assertRaises(StorageError):Executor(self.engine,None)
        result=self.execute()
        self.assertTrue(result['unlinked_now']);self.assertFalse(self.body.exists())
        self.assertEqual(self.executor.journal.get(self.contract['gc_job_id'])['phase'],'DONE')
        again=self.execute();self.assertTrue(again['replayed']);self.assertFalse(again['unlinked_now'])
        self.assertEqual(again['logical_bytes_removed_now'],0)
        self.engine.close();self.engine=StorageEngine(self.base/'private',self.node_id)
        self.executor=fixture_executor(self.engine,self.volume)
        self.assertTrue(self.execute()['replayed'])

    def test_populated_native_volume_cannot_be_adopted(self):
        from asc.replication.arena import fixture_node_capability
        volume=self.engine.volumes.register(self.base/'other',quota=1024**2,reserve=0)['volume_id']
        (self.base/'other'/'objects'/(uid()+'.blob')).write_bytes(b'unknown native data')
        with self.assertRaises(StorageError) as caught:fixture_node_capability(self.engine,volume)
        self.assertEqual(caught.exception.code,'gc_existing_volume_not_adopted')
        self.assertTrue(self.body.exists())

    def test_every_pre_unlink_crash_keeps_original_and_requires_fresh_authority_on_retry(self):
        for point in ('after_journal_prepare','after_delete_intent','before_final_authorize'):
            self.executor.fault_hook=lambda p,stop=point:(_ for _ in ()).throw(SimulatedCrash()) if p==stop else None
            with self.subTest(point=point),self.assertRaises(SimulatedCrash):self.execute()
            self.assertEqual(self.body.read_bytes(),self.data)
        self.executor.fault_hook=None;self.authorize.side_effect=StorageError('no_quorum',503)
        with self.assertRaises(StorageError):self.execute()
        self.assertTrue(self.body.exists())
        self.authorize.side_effect=self.authority;self.assertTrue(self.execute()['unlinked_now'])

    def test_actual_unlink_crash_lost_ack_and_manifest_restart_are_idempotent(self):
        self.executor.fault_hook=lambda p:(_ for _ in ()).throw(SimulatedCrash()) if p=='after_unlink' else None
        with self.assertRaises(SimulatedCrash):self.execute()
        self.assertFalse(self.body.exists())
        self.assertEqual(self.executor.journal.get(self.contract['gc_job_id'])['phase'],'DELETING')
        self.engine.close();self.engine=StorageEngine(self.base/'private',self.node_id)
        self.executor=fixture_executor(self.engine,self.volume)
        self.assertTrue(self.execute()['replayed'])
        with self.engine.manifest.connect() as db:
            self.assertIsNone(db.execute('SELECT * FROM files WHERE file_id=?',(self.file['file_id'],)).fetchone())

    def test_changed_scope_corrupt_bytes_and_unknown_absence_never_unlink(self):
        for field,value in [('node_id',uid()),('volume_id',uid()),('logical_path','../../outside'),('sha256','0'*64)]:
            contract={**self.contract,field:value}
            with self.subTest(field=field),self.assertRaises(StorageError):self.executor.execute(contract,self.authorize)
            self.assertTrue(self.body.exists())
        self.body.write_bytes(b'X'*len(self.data))
        with self.assertRaises(StorageError) as caught:self.execute()
        self.assertEqual(caught.exception.code,'gc_checksum_mismatch');self.assertTrue(self.body.exists())
        self.body.unlink()
        with self.assertRaises(StorageError) as caught:self.execute()
        self.assertEqual(caught.exception.code,'gc_unknown_absence')

    def test_links_and_volume_replacement_are_rejected_before_unlink(self):
        other=self.base/'other-body';other.write_bytes(self.data)
        self.body.unlink();self.body.symlink_to(other)
        with self.assertRaises(StorageError):self.execute()
        self.assertEqual(other.read_bytes(),self.data)
        self.body.unlink();os.link(other,self.body)
        with self.assertRaises(StorageError):self.execute()
        self.assertEqual(other.read_bytes(),self.data)

    def test_stale_or_slow_final_authority_cannot_unlink(self):
        self.authorize.side_effect=StorageError('stale_authority',409)
        with self.assertRaises(StorageError):self.execute()
        self.assertTrue(self.body.exists())
        self.authorize.side_effect=self.authority
        original=self.executor._authorize
        def stale(*args):return original(*args)-1
        with mock.patch.object(self.executor,'_authorize',side_effect=stale):
            with self.assertRaises(StorageError) as caught:self.execute()
        self.assertEqual(caught.exception.code,'gc_authority_budget_expired')
        self.assertTrue(self.body.exists())

    def test_root_and_objects_directory_replacement_preserve_both_media(self):
        original=self.base/'volume';moved=self.base/'retained-volume'
        original.rename(moved);original.mkdir()
        for folder in ('objects','staging'):(original/folder).mkdir()
        (original/'.asc-volume.json').write_bytes((moved/'.asc-volume.json').read_bytes())
        with self.assertRaises(StorageError):self.execute()
        self.assertEqual((moved/'objects'/self.body.name).read_bytes(),self.data)

    def test_unknown_absence_and_corrupt_journal_do_not_claim_reclamation(self):
        self.executor.fault_hook=lambda p:(_ for _ in ()).throw(SimulatedCrash()) if p=='after_journal_prepare' else None
        with self.assertRaises(SimulatedCrash):self.execute()
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.executor.journal.path)) as db,db:
            db.execute("UPDATE entries SET sha256=?",('0'*64,))
        self.executor.fault_hook=None
        with self.assertRaises(StorageError) as caught:self.execute()
        self.assertEqual(caught.exception.code,'gc_journal_quarantined')
        self.assertEqual(self.body.read_bytes(),self.data)

    def test_manifest_update_and_completed_journal_crashes_do_not_repeat_unlink(self):
        self.executor.fault_hook=lambda p:(_ for _ in ()).throw(SimulatedCrash()) if p=='after_manifest_update' else None
        with self.assertRaises(SimulatedCrash):self.execute()
        self.assertFalse(self.body.exists())
        self.engine.close();self.engine=StorageEngine(self.base/'private',self.node_id)
        self.executor=fixture_executor(self.engine,self.volume)
        self.assertTrue(self.execute()['replayed'])
        self.assertGreaterEqual(self.authorize.call_count,2)

    def test_lost_ack_after_durable_done_uses_fresh_authority_and_retains_reappeared_body(self):
        self.executor.fault_hook=lambda p:(_ for _ in ()).throw(SimulatedCrash()) if p=='after_journal_done' else None
        with self.assertRaises(SimulatedCrash):self.execute()
        self.assertFalse(self.body.exists())
        self.executor.fault_hook=None
        self.assertTrue(self.execute()['replayed'])
        self.assertEqual(self.authorize.call_count,2)
        self.body.write_bytes(b'new unknown data at old name')
        with self.assertRaises(StorageError) as caught:self.execute()
        self.assertEqual(caught.exception.code,'gc_deleted_object_reappeared')
        self.assertEqual(self.body.read_bytes(),b'new unknown data at old name')
