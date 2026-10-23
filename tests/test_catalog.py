"""Catalog/migration/cache/queue invariants, isolated from real devices."""
import copy
import hashlib
import io
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from asc.store import Registry, SCHEMA_VERSION
from asc.catalog.common import CatalogError, digest, now, uid
from asc.catalog.state import Catalog, insert
from asc.catalog.queue import JobQueue
from asc.catalog.metadata import MetadataSource, MetadataReplica
from asc.catalog.placement import candidates
from asc.catalog import grants
from asc.storage.engine import StorageEngine


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)
        self.reg=Registry(self.home/'registry.sqlite3');self.reg.initialize('cluster')
        self.catalog=Catalog(self.reg);self.queue=JobQueue(self.catalog)
        self.nodes=[]
        for index in range(3):
            node=self.reg.join(self.reg.add_pair_code(),'node-'+str(index),{'protected':False})
            volume=uid()
            caps={'max_upload_bytes':1024**2,'volumes':[{'volume_id':volume,'state':'online','writable':True,
                'readable':True,'free_bytes':1024**2,'quota':1024**2,'reserve':0,'used_bytes':0}]}
            with self.reg.connect() as db:
                insert(db,'catalog_nodes',{'node_id':node['node_id'],'origin':'https://127.0.0.1:9443','pin':'A'*64,
                    'device_id':'physical-'+str(index),'metadata_allowed':1,'storage_allowed':1,
                    'approved_generation':1,'volume_ids':json.dumps([volume]),'capabilities':json.dumps(caps),'checked_at':now()})
            self.nodes.append({**node,'volume_id':volume})
        self.sha=hashlib.sha256(b'test').hexdigest()

    def create(self,policy='replicated_2',key='catalog_request_01',path='docs/test.bin',version=1):
        return self.catalog.mutate('CREATE',{'idempotency_key':key,'logical_path':path,'size':4,'sha256':self.sha,
                                             'policy':policy,'version':version})

    def upload_job(self,file_id):
        with self.reg.connect() as db:
            return dict(db.execute("SELECT * FROM catalog_jobs WHERE file_id=? AND kind='UPLOAD'",(file_id,)).fetchone())

    def complete_upload(self,file_id):
        job=self.upload_job(file_id)
        self.queue.ack_upload(job['job_id'],uid(),uid())
        job=self.queue.claim()
        proof={'file_id':job['target_local_file_id'],'volume_id':job['target_volume_id'],'logical_path':job['logical_path'],
               'state':'COMMITTED','size':4,'sha256':self.sha,'physically_verified':True}
        return self.catalog.mutate('COMPLETE',{'job_id':job['job_id'],'run_token':job['run_token'],'proof':proof})

    def assert_code(self,code,fn):
        with self.assertRaises(CatalogError) as caught:fn()
        self.assertEqual(caught.exception.code,code)

    def test_global_idempotency_explicit_versions_and_no_false_replica_count(self):
        first=self.create();file_id=first['file']['file_id']
        self.assertEqual(self.create()['file']['file_id'],file_id)
        self.assert_code('idempotency_conflict',lambda:self.create(path='other'))
        self.assert_code('logical_version_exists',lambda:self.create(key='different_key'))
        other=self.create(key='new_version_key',version=2)
        self.assertNotEqual(other['file']['file_id'],file_id)
        report=self.catalog.file(file_id)
        self.assertEqual((report['desired_replicas'],report['verified_replicas'],report['available_replicas']),(2,0,0))
        self.complete_upload(file_id)
        self.assertEqual(self.catalog.file(file_id)['verified_replicas'],1)
        self.assertEqual(self.catalog.file(file_id)['protection'],'DEGRADED')

    def test_placement_excludes_protected_quota_unknown_stale_and_same_physical_device(self):
        with self.reg.connect() as db:
            db.execute('UPDATE nodes SET profile=? WHERE node_id=?',(json.dumps({'protected':True}),self.nodes[0]['node_id']))
            db.execute('UPDATE catalog_nodes SET checked_at=0 WHERE node_id=?',(self.nodes[1]['node_id'],))
            node=db.execute('SELECT capabilities FROM catalog_nodes WHERE node_id=?',(self.nodes[2]['node_id'],)).fetchone()
            caps=json.loads(node[0]);caps['volumes'][0]['free_bytes']=None
            db.execute('UPDATE catalog_nodes SET capabilities=? WHERE node_id=?',(json.dumps(caps),self.nodes[2]['node_id']))
            self.assertEqual(candidates(db,4),[])
        self.assert_code('no_eligible_storage',self.create)
        with self.reg.connect() as db:
            db.execute("UPDATE nodes SET profile='{}'")
            db.execute("UPDATE catalog_nodes SET checked_at=?,device_id='same-phone'",(now(),))
            self.assertTrue(candidates(db,4))
        file_id=self.create()['file']['file_id'];self.complete_upload(file_id)
        self.assertEqual(self.catalog.schedule(file_id),[])

    def test_snapshot_incremental_duplicate_gap_digest_and_rollback_are_atomic(self):
        source=MetadataSource(self.reg)
        replica=MetadataReplica(self.home/'node-cache'/'catalog.sqlite3','cluster')
        replica.install(source.snapshot())
        file_id=self.create()['file']['file_id']
        delta=source.changes(0);replica.apply(delta);replica.apply(delta)
        self.assertEqual(replica.file(file_id)['entry']['file']['sha256'],self.sha)
        self.assertEqual(replica.status()['revision'],1)
        self.catalog.mutate('POLICY',{'file_id':file_id,'policy':'replicated_3'})
        bad=source.changes(1);bad['events'][0]['revision']+=1
        self.assert_code('invalid_event_digest_or_order',lambda:replica.apply(bad))
        self.assertEqual(replica.status()['revision'],1)
        snapshot=source.snapshot();tampered=copy.deepcopy(snapshot);tampered['files'][0]['file']['sha256']='0'*64
        self.assert_code('snapshot_digest_mismatch',lambda:replica.install(tampered))
        self.assertEqual(replica.status()['revision'],1)
        replica.install(snapshot)
        old=copy.deepcopy(snapshot);old['revision']=1;old['files'][0]['file']['revision']=1;old['digest']=digest({k:v for k,v in old.items() if k!='digest'})
        self.assert_code('metadata_rollback_or_epoch_conflict',lambda:replica.install(old))
        self.assertEqual(replica.status()['revision'],2)
        self.assertTrue(replica.file(file_id)['metadata']['read_only'])

    def test_metadata_projection_contains_no_identity_keys_tokens_or_grants(self):
        self.create()
        raw=json.dumps(MetadataSource(self.reg).snapshot())
        for node in self.nodes:
            self.assertNotIn(node['token'],raw)
        for forbidden in ('token_hash','grant_hash','private_key','admin_token','run_token','upload_key'):
            self.assertNotIn(forbidden,raw)

    def test_upload_replay_keeps_original_fingerprint_after_policy_change(self):
        file_id=self.create()['file']['file_id']
        self.catalog.mutate('POLICY',{'file_id':file_id,'policy':'replicated_3'})
        replay=self.create()
        self.assertEqual(replay['file']['file_id'],file_id)
        self.assertEqual(replay['file']['policy'],'replicated_3')
        self.assert_code('idempotency_conflict',lambda:self.create(policy='replicated_3'))

    def test_history_retention_requires_snapshot_resync(self):
        replica=MetadataReplica(self.home/'cache'/'cache.sqlite3','cluster')
        replica.install(MetadataSource(self.reg).snapshot())
        self.create()
        with self.reg.connect() as db:db.execute('DELETE FROM catalog_events')
        self.assert_code('resync_required',lambda:MetadataSource(self.reg).changes(0))
        replica.install(MetadataSource(self.reg).snapshot())
        self.assertEqual(replica.status()['revision'],1)

    def test_readonly_cache_never_becomes_an_authoritative_writer(self):
        path=self.home/'cache'/'catalog.sqlite3'
        replica=MetadataReplica(path,'cluster');snap=MetadataSource(self.reg).snapshot();replica.install(snap)
        reader=MetadataReplica(path,'cluster',read_only=True)
        self.assert_code('read_only_metadata',lambda:reader.install(snap))
        self.assert_code('read_only_metadata',lambda:reader.apply(MetadataSource(self.reg).changes(0)))
        self.assertEqual(reader.files()['files'],[])
        with self.assertRaises(CatalogError):MetadataReplica(path,'other-cluster')

    def test_persistent_job_deduplication_and_crash_fences_old_grants(self):
        file_id=self.create()['file']['file_id'];self.complete_upload(file_id)
        jobs=self.catalog.schedule(file_id)
        self.assertEqual(len(jobs),1);self.assertEqual(self.catalog.schedule(file_id),[])
        job=self.queue.claim()
        token=grants.mint(self.reg,job['target_node_id'],job['target_volume_id'],'target',job=job)
        node=next(n for n in self.nodes if n['node_id']==job['target_node_id'])
        scope={'method':'POST','resource':'uploads'}
        self.assertIsNotNone(self.reg.storage_authorize(node['node_id'],node['token'],token,node['volume_id'],'write',scope))
        bound=self.queue.checkpoint(job,uid(),uid())
        self.queue.recover()
        self.assertIsNone(self.reg.storage_authorize(node['node_id'],node['token'],token,node['volume_id'],'write',scope))
        recovered=self.queue.claim()
        self.assertNotEqual(recovered['run_token'],job['run_token'])
        self.assertEqual(recovered['target_local_file_id'],bound['target_local_file_id'])
        self.assertEqual(next(j['state'] for j in self.queue.list()['jobs'] if j['job_id']==job['job_id']),'RUNNING')

    def test_scoped_grant_expiry_wrong_file_revoke_and_replay_are_denied(self):
        node=self.nodes[0];local_id=uid()
        token=grants.mint(self.reg,node['node_id'],node['volume_id'],'read',local_file_id=local_id)
        auth=lambda resource,op='read':self.reg.storage_authorize(node['node_id'],node['token'],token,node['volume_id'],op,
                                                                 {'method':'GET','resource':resource})
        self.assertIsNotNone(auth('files/'+local_id+'/content'))
        self.assertIsNone(auth('files/'+uid()+'/content'))
        self.assertIsNone(auth('uploads','write'))
        with self.reg.connect() as db:db.execute('UPDATE transfer_grants SET expires_at=1')
        self.assertIsNone(auth('files/'+local_id))
        token=grants.mint(self.reg,node['node_id'],node['volume_id'],'read',local_file_id=local_id)
        self.reg.revoke(node['node_id'])
        self.assertIsNone(auth('files/'+local_id))

    def test_backoff_timeout_and_failure_preserve_replica_metadata(self):
        file_id=self.create()['file']['file_id'];self.complete_upload(file_id);self.catalog.schedule(file_id)
        job=self.queue.claim();self.queue.failed_attempt(job,'transfer_unavailable')
        saved=self.queue.get(job['job_id'])
        self.assertEqual(saved['state'],'RETRY');self.assertGreater(saved['next_attempt_at'],now())
        self.assertIsNone(self.queue.claim())
        self.assertEqual(self.catalog.file(file_id)['verified_replicas'],1)
        with self.reg.connect() as db:db.execute('UPDATE catalog_jobs SET next_attempt_at=0 WHERE job_id=?',(job['job_id'],))
        retry=self.queue.claim()
        self.assertEqual(retry['job_id'],job['job_id']);self.assertEqual(retry['attempts'],2)
        with self.reg.connect() as db:db.execute('UPDATE catalog_jobs SET lease_until=0 WHERE job_id=?',(job['job_id'],))
        self.assertIsNone(self.queue.claim())
        self.assertEqual(self.queue.get(job['job_id'])['last_error'],'job_timeout')

    def test_migration_three_preserves_identity_grants_manifest_and_committed_bytes(self):
        node=self.nodes[0]
        grant=self.reg.storage_grant(node['node_id'],node['volume_id'],['read'])
        with StorageEngine(self.home/'private','legacy-node') as engine:
            volume=engine.volumes.register(self.home/'data',reserve=0)['volume_id']
            session=engine.initiate('owner',volume,'legacy_request','legacy.bin',4,self.sha)
            engine.upload(session['session_id'],'owner',volume,io.BytesIO(b'test'),4)
            file=engine.commit(session['session_id'],'owner',volume)
        before=self.reg.detail(node['node_id'])
        with self.reg.connect() as db:
            for name in ('catalog_state','catalog_nodes','catalog_files','catalog_replicas','catalog_events','catalog_jobs','catalog_job_history','transfer_grants'):
                db.execute('DROP TABLE '+name)
            db.execute('PRAGMA user_version=3')
        self.reg.initialize('cluster')
        self.assertEqual(self.reg.detail(node['node_id']),before)
        self.assertIsNotNone(self.reg.storage_authorize(node['node_id'],node['token'],grant['grant'],node['volume_id'],'read'))
        with StorageEngine(self.home/'private','legacy-node') as engine:
            with engine.download(file['file_id'],volume) as (_,stream):self.assertEqual(stream.read(),b'test')
        with self.reg.connect() as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],SCHEMA_VERSION)

    def test_migration_failure_rolls_back_new_schema_without_losing_old_identity(self):
        from unittest import mock
        with self.reg.connect() as db:db.execute('PRAGMA user_version=3')
        def fail(db):
            db.execute('CREATE TABLE migration_partial(value TEXT)')
            raise RuntimeError('injected migration fault')
        with mock.patch('asc.catalog.schema.migrate',side_effect=fail):
            with self.assertRaises(RuntimeError):self.reg.initialize('cluster')
        with self.reg.connect() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='migration_partial'").fetchone())
        self.assertTrue(self.reg.heartbeat(self.nodes[0]['node_id'],self.nodes[0]['token'],{}))

    def test_readonly_wrong_cluster_and_self_consistent_conflicting_snapshot_are_rejected(self):
        file_id=self.create()['file']['file_id']
        source=MetadataSource(self.reg);snapshot=source.snapshot()
        path=self.home/'cache'/'catalog.sqlite3'
        replica=MetadataReplica(path,'cluster');replica.install(snapshot)
        with self.assertRaises(CatalogError):MetadataReplica(path,'other-cluster',read_only=True)
        changed=copy.deepcopy(snapshot)
        changed['files'][0]['file']['logical_path']='forged/label'
        changed['digest']=digest({k:v for k,v in changed.items() if k!='digest'})
        self.assert_code('snapshot_checkpoint_conflict',lambda:replica.install(changed))
        self.assertEqual(replica.file(file_id)['entry']['file']['logical_path'],'docs/test.bin')

    def test_removed_volume_is_not_counted_as_a_readable_source_or_placement(self):
        file_id=self.create()['file']['file_id'];self.complete_upload(file_id)
        replica=self.catalog.file(file_id)['replicas'][0]
        with self.reg.connect() as db:
            row=db.execute('SELECT capabilities FROM catalog_nodes WHERE node_id=?',(replica['node_id'],)).fetchone()
            caps=json.loads(row[0]);caps['volumes'][0].update(state='unavailable',readable=None,writable=None)
            db.execute('UPDATE catalog_nodes SET capabilities=? WHERE node_id=?',(json.dumps(caps),replica['node_id']))
        self.assertEqual(self.catalog.file(file_id)['available_replicas'],0)
        self.assertEqual(self.catalog.schedule(file_id),[])

    def test_repeated_failure_state_keeps_same_revision_materialization(self):
        from unittest import mock
        file_id=self.create()['file']['file_id'];self.complete_upload(file_id)
        replica=self.catalog.file(file_id)['replicas'][0]
        self.catalog.mutate('REPLICA_STATE',{'replica_id':replica['replica_id'],'state':'CORRUPT'})
        source=MetadataSource(self.reg);cache=MetadataReplica(self.home/'cached'/'cache.sqlite3','cluster')
        cache.install(source.snapshot());before=cache.status()['revision']
        with mock.patch('asc.catalog.state.now',return_value=now()+100):
            self.catalog.mutate('REPLICA_STATE',{'replica_id':replica['replica_id'],'state':'CORRUPT'})
        cache.install(source.snapshot())
        self.assertEqual(cache.status()['revision'],before)

    def test_known_schema_four_never_recreates_missing_epoch_authority(self):
        file_id=self.create()['file']['file_id']
        with self.reg.connect() as db:db.execute('DROP TABLE catalog_state')
        with self.assertRaises(ValueError):self.reg.initialize('cluster')
        with self.reg.connect() as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='catalog_state'").fetchone())
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT file_id FROM catalog_files').fetchone()[0],file_id)
        self.assertTrue(self.reg.heartbeat(self.nodes[0]['node_id'],self.nodes[0]['token'],{}))
