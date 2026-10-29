"""Exact GC authorization tests. Unit receipts are explicit fakes; no real volumes."""
import copy
import hashlib
import json
import secrets
import unittest
from types import SimpleNamespace
from unittest import mock

from asc.catalog.common import CatalogError, canonical, digest, uid
from asc.client import ClientError
from asc.failover import state
from asc.failover.runtime import RuntimeRegistry
from asc.replication.execution import contract
from tests import test_replication as fixtures


class GCAuthorizationTests(unittest.TestCase):
    def setUp(self):
        holder=fixtures.GCReservationTests();holder.setUp();self.addCleanup(holder.doCleanups)
        self.holder=holder;self.runtime=holder.runtime;self.service=holder.service;self.gc=holder.gc
        self.service.gc_test_context=holder.capability;self.service.timeout=30
        prepared=holder.prepare()
        self.job_id=self.gc.confirm({'request_id':'confirm-auth-test','plan_id':prepared['plan_id'],
                                    'confirmation':prepared['required_confirmation']})['gc_job_id']
        self.token=secrets.token_urlsafe(40)
        target_id=self.runtime.doc['replication']['retired'][holder.holder.source['replica_id']]['replica']['node_id']
        next(n for n in self.runtime.doc['tables']['nodes'] if n['node_id']==target_id)['token_hash']=hashlib.sha256(self.token.encode()).hexdigest()
        original=self.runtime.commit
        def commit(view,doc,*args):
            from asc.replication.state import transition
            transition(view['document'],doc)
            original(view,doc,*args)
            return {'term':doc['authority']['term'],'index':self.runtime.index}
        self.runtime.commit=mock.Mock(side_effect=commit)

    def issue(self):
        self.raw,self.exact,self.target=self.gc.issue(self.job_id)
        return self.raw,self.exact,self.target

    def authorize(self,**changes):
        obj={'node_id':self.exact['node_id'],'node_token':self.token,'grant':self.raw,
             'volume_id':self.exact['volume_id'],'scope':{'method':'POST','resource':'gc/'+self.job_id},'nonce':uid()}
        obj.update(changes)
        return self.gc.authorize(**obj)

    def result(self,exact=None,replay=False):
        exact=exact or self.exact
        return {k:exact[k] for k in ('gc_job_id','node_id','volume_id','local_file_id','size','sha256')}|{
            'state':'DONE','physical_deletions':1,'unlinked_now':not replay,'replayed':replay,
            'logical_bytes_removed_now':0 if replay else exact['size']}

    def test_issue_is_committed_hash_only_and_exact_nonce_authority_reproves_bytes(self):
        self.issue();before=self.service._proof.call_count
        reply=self.authorize();self.assertGreater(self.service._proof.call_count,before)
        self.assertEqual(reply['constraints'],self.exact)
        self.assertEqual(reply['authority']['term'],4)
        self.assertNotIn(self.raw.encode(),canonical(self.runtime.doc))
        call=self.runtime.commit.call_args
        expected=digest({'node_id':self.exact['node_id'],'grant_sha256':hashlib.sha256(self.raw.encode()).hexdigest(),
                         'volume_id':self.exact['volume_id'],'operation':'gc',
                         'scope':{'method':'POST','resource':'gc/'+self.job_id},'nonce':reply['authority']['nonce']})
        self.assertEqual(call.args[3],expected)
        self.assertEqual(reply['authority']['intent_sha256'],expected)

    def test_wrong_node_volume_grant_method_resource_and_legacy_scope_are_denied(self):
        self.issue()
        for change in ({'node_id':uid()},{'volume_id':uid()},{'node_token':secrets.token_urlsafe(40)},
                       {'grant':secrets.token_urlsafe(40)},{'scope':None},
                       {'scope':{'method':'GET','resource':'gc/'+self.job_id}},
                       {'scope':{'method':'POST','resource':'files/'+self.exact['local_file_id']}},
                       {'scope':{'method':'POST','resource':'gc/'+uid()}},
                       {'scope':{'method':'POST','resource':'gc/'+self.job_id,'object':uid()}}):
            with self.subTest(change=tuple(change)),self.assertRaises(CatalogError):self.authorize(**change)

    def test_generation_endpoint_revoke_and_protection_changes_cannot_inherit_permit(self):
        self.issue();before=copy.deepcopy(self.runtime.doc)
        for change in ('generation','endpoint','revoke','protected'):
            self.runtime.doc=copy.deepcopy(before)
            node=next(n for n in self.runtime.doc['tables']['nodes'] if n['node_id']==self.exact['node_id'])
            approved=next(n for n in self.runtime.doc['tables']['catalog_nodes'] if n['node_id']==self.exact['node_id'])
            if change=='generation':node['token_version']+=1;approved['approved_generation']+=1
            if change=='endpoint':approved['pin']='F'*64
            if change=='revoke':node['state']='revoked'
            if change=='protected':node['profile']='{"protected":true}'
            with self.subTest(change=change),self.assertRaises(CatalogError):self.authorize()

    def test_expired_replaced_run_takeover_and_missing_quorum_deny_authorization(self):
        self.issue();old=self.raw
        with mock.patch('asc.replication.execution.now',return_value=self.exact['permit_expires_at']):
            with self.assertRaises(CatalogError):self.authorize()
        self.issue()
        with self.assertRaises(CatalogError):self.authorize(grant=old)
        with mock.patch.object(self.runtime,'commit',side_effect=CatalogError('no_quorum',503)):
            with self.assertRaises(CatalogError):self.authorize()
        self.runtime.doc=state.takeover(self.runtime.doc,'voter-b',5)
        with self.assertRaises(CatalogError):self.authorize()

    def test_new_trash_pin_missing_survivor_and_corruption_hold_target(self):
        from asc.backup.state import empty
        self.issue();before=copy.deepcopy(self.runtime.doc)
        self.runtime.doc['backup']=empty()
        self.runtime.doc['backup']['files'][self.exact['file_id']]={'state':'TRASH','changed_at':1,'retain_until':2}
        with self.assertRaises(CatalogError):self.authorize()
        self.runtime.doc=copy.deepcopy(before)
        self.runtime.doc['catalog']['replicas'].clear()
        with self.assertRaises(CatalogError):self.authorize()
        self.runtime.doc=before;self.service._proof.side_effect=CatalogError('checksum_mismatch',422)
        with self.assertRaises(CatalogError):self.authorize()

    def test_policy_or_term_change_during_stream_proof_is_rechecked(self):
        self.issue();before=copy.deepcopy(self.runtime.doc)
        def changed(*args):
            self.runtime.doc['catalog']['files'][0]['policy']='replicated_3'
            return {'physically_verified':True}
        self.service._proof.side_effect=changed
        with self.assertRaises(CatalogError):self.authorize()
        self.runtime.doc=before
        def takeover(*args):
            self.runtime.doc=state.takeover(self.runtime.doc,'voter-b',5)
            return {'physically_verified':True}
        self.service._proof.side_effect=takeover
        with self.assertRaises(CatalogError):self.authorize()

    def test_explicit_execute_checks_exact_completion_and_is_idempotent(self):
        def send(method,path,obj):
            self.exact=contract(self.runtime.doc,self.runtime.doc['replication']['gc_jobs'][self.job_id])
            return self.result()
        with mock.patch('asc.replication.execution.StorageClient') as client:
            client.return_value.json.side_effect=send
            first=self.gc.execute({'gc_job_id':self.job_id})
            self.assertEqual(first['state'],'DONE')
            self.assertEqual(self.gc.execute({'gc_job_id':self.job_id}),first)
            client.return_value.json.assert_called_once()
        state.validate(self.runtime.doc)

    def test_lost_ack_reissues_same_job_new_permit_and_accepts_journal_replay(self):
        with mock.patch('asc.replication.execution.StorageClient') as client:
            client.return_value.json.side_effect=ClientError('lost synthetic ACK',503)
            with self.assertRaises(CatalogError):self.gc.execute({'gc_job_id':self.job_id})
            first=copy.deepcopy(self.runtime.doc['replication']['gc_jobs'][self.job_id])
            def replay(*args):
                self.exact=contract(self.runtime.doc,self.runtime.doc['replication']['gc_jobs'][self.job_id])
                return self.result(replay=True)
            client.return_value.json.side_effect=replay
            self.assertEqual(self.gc.execute({'gc_job_id':self.job_id})['state'],'DONE')
            last=self.runtime.doc['replication']['gc_jobs'][self.job_id]
            self.assertEqual(last['attempts'],2);self.assertNotEqual(last['run_id'],first['run_id'])
            self.assertEqual(last['plan_sha256'],first['plan_sha256'])

    def test_false_ack_or_permit_replacement_during_ack_never_completes(self):
        with mock.patch('asc.replication.execution.StorageClient') as client:
            client.return_value.json.return_value={'state':'DONE'}
            with self.assertRaises(CatalogError):self.gc.execute({'gc_job_id':self.job_id})
            self.assertEqual(self.runtime.doc['replication']['gc_jobs'][self.job_id]['state'],'RUNNING')
            def raced(*args):
                self.exact=contract(self.runtime.doc,self.runtime.doc['replication']['gc_jobs'][self.job_id])
                reply=self.result();self.gc.issue(self.job_id);return reply
            client.return_value.json.side_effect=raced
            with self.assertRaises(CatalogError):self.gc.execute({'gc_job_id':self.job_id})
            self.assertEqual(self.runtime.doc['replication']['gc_jobs'][self.job_id]['state'],'RUNNING')

    def test_survivor_endpoint_change_during_proof_denies_issue_and_authorize(self):
        self.issue();before=copy.deepcopy(self.runtime.doc)
        survivor=before['catalog']['replicas'][0]['node_id']
        for operation in ('issue','authorize'):
            self.runtime.doc=copy.deepcopy(before)
            def changed(*args):
                next(n for n in self.runtime.doc['tables']['catalog_nodes'] if n['node_id']==survivor)['pin']='F'*64
                return {'physically_verified':True}
            self.service._proof.side_effect=changed
            with self.subTest(operation=operation),self.assertRaises(CatalogError) as denied:
                self.gc.issue(self.job_id) if operation=='issue' else self.authorize()
            self.assertEqual(denied.exception.code,'stale_gc_proof')

    def test_new_reference_during_stream_proof_denies_final_authority(self):
        from asc.backup.state import empty
        self.issue()
        def pinned(*args):
            self.runtime.doc['backup']=empty()
            self.runtime.doc['backup']['files'][self.exact['file_id']]={'state':'TRASH','changed_at':1,'retain_until':2}
            return {'physically_verified':True}
        self.service._proof.side_effect=pinned
        with self.assertRaises(CatalogError) as denied:self.authorize()
        self.assertEqual(denied.exception.code,'stale_gc_proof')

    def test_volatile_telemetry_is_not_authority_but_protection_change_is(self):
        self.issue();before=copy.deepcopy(self.runtime.doc)
        survivor=before['catalog']['replicas'][0]['node_id']
        for protected in (False,True):
            self.runtime.doc=copy.deepcopy(before)
            def heartbeat(*args):
                node=next(n for n in self.runtime.doc['tables']['nodes'] if n['node_id']==survivor)
                profile=json.loads(node['profile']);profile.update(protected=protected,storage={'free_bytes':123,'checked_at':456})
                node['profile']=json.dumps(profile)
                return {'physically_verified':True}
            self.service._proof.side_effect=heartbeat
            with self.subTest(protected=protected):
                if protected:
                    with self.assertRaises(CatalogError) as denied:self.authorize()
                    self.assertEqual(denied.exception.code,'stale_gc_proof')
                else:self.assertEqual(self.authorize()['constraints'],self.exact)

    def test_fixed_gc_errors_are_actionable_and_unknown_error_text_stays_redacted(self):
        from asc.client import request_json
        for label in ('stale_gc_plan','gc_plan_expired','stale_gc_proof','gc_execution_unconfirmed','arbitrary-private-detail'):
            response=mock.Mock(status=409)
            response.read.return_value=json.dumps({'error':label}).encode()
            with mock.patch('asc.client.connect_pinned') as connect:
                connect.return_value.getresponse.return_value=response
                with self.assertRaises(ClientError) as rejected:
                    request_json('https://127.0.0.1:9443','A'*64,'POST','/synthetic',{})
            self.assertEqual(rejected.exception.code,'request_failed' if label=='arbitrary-private-detail' else label)

    def test_retained_snapshots_and_backup_jobs_block_final_authority(self):
        from asc.backup.state import empty,capture
        from asc.catalog.common import now
        self.issue();before=copy.deepcopy(self.runtime.doc)
        for pin in ('snapshot','backup-job'):
            self.runtime.doc=copy.deepcopy(before);backup=empty();self.runtime.doc['backup']=backup
            if pin=='snapshot':
                snapshot=capture(self.runtime.view(),backup,now(),60)
                backup['snapshots'][uid()]=snapshot
            else:
                backup['jobs'][uid()]={'kind':'RESTORE','source_file_id':self.exact['file_id'],'target_file_id':None,'snapshot_id':None,'proofs':[]}
            with self.subTest(pin=pin),self.assertRaises(CatalogError):self.authorize()

    def test_slow_network_authority_reply_is_rejected_before_local_boundary(self):
        from asc.replication.sandbox import Executor
        from asc.storage.errors import StorageError
        self.issue();reply=self.authorize()
        executor=object.__new__(Executor)
        with mock.patch('asc.replication.sandbox.time.monotonic',side_effect=[0,11]):
            with self.assertRaises(StorageError) as denied:executor._authorize(self.exact,lambda:reply)
        self.assertEqual(denied.exception.code,'gc_authority_budget_expired')

    def test_default_context_and_registry_gc_dispatch_have_no_legacy_fallback(self):
        self.service.gc_test_context=None
        with self.assertRaises(CatalogError):self.gc.issue(self.job_id)
        runtime=SimpleNamespace(path='synthetic-unused');reg=RuntimeRegistry(runtime)
        args=(uid(),secrets.token_urlsafe(40),secrets.token_urlsafe(40),uid(),'gc',{},uid())
        with self.assertRaises(CatalogError):reg.storage_authorize(*args)
        runtime.gc_authorizer=SimpleNamespace(authorize=mock.Mock(side_effect=CatalogError('no_quorum',503)))
        with self.assertRaises(CatalogError):reg.storage_authorize(*args)
        runtime.gc_authorizer.authorize.assert_called_once()


if __name__=='__main__':unittest.main()
