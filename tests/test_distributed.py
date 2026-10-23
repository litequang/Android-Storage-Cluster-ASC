"""Phase 1.2B real three-node pinned HTTPS acceptance; no phone or real user state."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import ssl
import threading
import unittest
from unittest import mock
from asc import cli
from asc.client import ClientError,request_json
from asc.catalog.client import ClusterClient
from asc.catalog.common import CatalogError,now,uid
from asc.catalog.metadata import MetadataReplica,synchronize
from asc.catalog.service import CatalogService
from asc.server import Server
from asc.storage.client import StorageClient
from asc.storage.runtime import StorageRuntime
from tests import test_storage_cluster as storage_fixtures


class SimulatedCrash(BaseException):
    pass


class DistributedTests(unittest.TestCase):
    stop_controller=storage_fixtures.ClusterTests.stop_controller
    controller=storage_fixtures.ClusterTests.controller
    owner=storage_fixtures.ClusterTests.owner
    assert_status=storage_fixtures.ClusterTests.assert_status

    def setUp(self):
        storage_fixtures.ClusterTests.setUp(self)
        self.service=CatalogService(self.reg).start()
        self.addCleanup(lambda:self.service.close())
        self.server.catalog=self.service
        self.global_client=ClusterClient(self.origin,self.pin,self.admin)
        for node in self.nodes:
            self.global_client.request('POST','nodes/register',{'node_id':node['cfg']['node_id'],
                'origin':'https://127.0.0.1:'+str(node['port']),'pin':node['pin'],'device_id':node['name'],
                'volume_ids':[node['volume']]})

    def upload_global(self,policy='replicated_2',key='global_upload_01',path='cluster/report.bin'):
        result=self.global_client.upload(io.BytesIO(self.data),path,key,policy)
        self.assertEqual(result['job_state'],'COMPLETED')
        return result['file']['file']['file_id']

    def drain(self,limit=10):
        for _ in range(limit):
            job=self.service.run_one()
            if job is None:break
            self.assertEqual(job['state'],'COMPLETED',job.get('last_error'))

    def node_for(self,node_id):
        return next(n for n in self.nodes if n['cfg']['node_id']==node_id)

    def physical(self,replica):
        node=self.node_for(replica['node_id'])
        return self.base/str(self.nodes.index(node))/'data'/'objects'/(replica['local_file_id']+'.blob')

    def restart_controller(self):
        self.service.close()
        port=self.server.server_address[1];context=self.server.tls_context
        self.stop_controller()
        from asc.store import Registry
        self.reg=Registry(self.base/'controller'/'registry.sqlite3')
        self.reg.initialize('test-cluster')
        self.service=CatalogService(self.reg).start()
        self.server=Server(('127.0.0.1',port),self.reg,self.admin,catalog=self.service)
        self.server.tls_context=context
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def test_independent_copies_metadata_all_nodes_and_download_fallback(self):
        file_id=self.upload_global();self.drain()
        entry=self.service.catalog.file(file_id)
        self.assertEqual((entry['desired_replicas'],entry['verified_replicas'],entry['available_replicas']),(2,2,2))
        replicas=entry['replicas'];self.assertEqual(len(replicas),2)
        self.assertNotEqual(replicas[0]['node_id'],replicas[1]['node_id'])
        for replica in replicas:
            self.assertEqual(hashlib.sha256(self.physical(replica).read_bytes()).hexdigest(),self.sha)
        for node in self.nodes:
            status=synchronize(node['private'],node['cfg'])
            self.assertEqual(status['lag'],0)
            cache=MetadataReplica(node['private']/'catalog-metadata.sqlite3','test-cluster',read_only=True)
            self.assertEqual(len(cache.file(file_id)['entry']['replicas']),2)
        plan=self.global_client.request('POST','files/'+file_id+'/download',{})
        primary=self.node_for(plan['candidates'][0]['node_id'])
        primary['runtime'].__exit__(None,None,None)
        # Both were valid at plan time; the actual first HTTP endpoint now fails.
        with mock.patch.object(self.global_client,'request',return_value=plan):
            output=io.BytesIO();result=self.global_client.download(file_id,output)
        self.assertEqual(output.getvalue(),self.data)
        self.assertNotEqual(result['node_id'],primary['cfg']['node_id'])
        primary['runtime']=StorageRuntime(primary['private'],primary['cfg']).__enter__()

    def test_offline_metadata_catches_up_and_controller_offline_cache_is_readonly(self):
        file_id=self.upload_global('single')
        node=self.nodes[2];synchronize(node['private'],node['cfg'])
        old=MetadataReplica(node['private']/'catalog-metadata.sqlite3','test-cluster',read_only=True).status()['revision']
        node['runtime'].__exit__(None,None,None)
        self.global_client.request('POST','files/'+file_id+'/policy',{'policy':'replicated_3'})
        node['runtime']=StorageRuntime(node['private'],node['cfg']).__enter__()
        self.service.reconcile()
        self.drain()
        current=synchronize(node['private'],node['cfg'])
        self.assertGreater(current['revision'],old);self.assertEqual(current['lag'],0)
        cache=MetadataReplica(node['private']/'catalog-metadata.sqlite3','test-cluster',read_only=True)
        self.stop_controller()
        try:
            cached=cache.file(file_id)
            self.assertTrue(cached['metadata']['stale'])
            self.assertEqual(len(cached['entry']['replicas']),3)
            self.assertIsNone(cached['available_replicas'])
            with self.assertRaises(CatalogError):cache.install({})
        finally:
            context=self.server.tls_context;port=self.server.server_address[1]
            self.server=Server(('127.0.0.1',port),self.reg,self.admin,catalog=self.service);self.server.tls_context=context
            self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def test_corrupt_replica_is_preserved_and_replaced_after_reconciliation(self):
        file_id=self.upload_global();self.drain()
        entry=self.service.catalog.file(file_id);damaged=entry['replicas'][0]
        physical=self.physical(damaged);physical.write_bytes(b'corrupt bytes')
        report=self.global_client.request('POST','reconcile',{})
        self.assertGreaterEqual(report['checked'],2)
        self.assertTrue(physical.exists())
        self.drain()
        healed=self.service.catalog.file(file_id)
        self.assertEqual(healed['verified_replicas'],2)
        self.assertEqual(len(healed['replicas']),3)  # Suspect copy remains recorded and preserved.
        self.assertEqual(next(r['state'] for r in healed['replicas'] if r['replica_id']==damaged['replica_id']),'CORRUPT')
        output=io.BytesIO();self.global_client.download(file_id,output)
        self.assertEqual(output.getvalue(),self.data)

    def test_controller_crash_after_target_commit_retries_without_duplicate_object(self):
        file_id=self.upload_global()
        def crash(phase,job):
            if phase=='after_commit':raise SimulatedCrash()
        self.service.fault_hook=crash
        with self.assertRaises(SimulatedCrash):self.service.run_one()
        with self.reg.connect() as db:
            job=dict(db.execute("SELECT * FROM catalog_jobs WHERE kind='COPY'").fetchone())
        self.assertEqual(job['state'],'RUNNING')
        target=self.node_for(job['target_node_id'])
        with target['runtime'].engine.manifest.connect() as db:
            count_before=db.execute('SELECT COUNT(*) FROM files').fetchone()[0]
        self.assertTrue((self.base/str(self.nodes.index(target))/'data'/'objects'/(job['target_local_file_id']+'.blob')).exists())
        self.restart_controller()
        retried=self.service.run_one()
        self.assertEqual(retried['job_id'],job['job_id']);self.assertEqual(retried['state'],'COMPLETED')
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],2)
        with target['runtime'].engine.manifest.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM files').fetchone()[0],count_before)
        self.assertIsNone(self.service.run_one())

    def test_transfer_scope_revoke_unauthorized_catalog_and_fake_ack(self):
        self.assert_status(401,lambda:request_json(self.origin,self.pin,'GET','/catalog/v1/files',token=self.nodes[0]['cfg']['token']))
        self.assert_status(401,lambda:request_json(self.origin,self.pin,'POST','/catalog/v1/files/'+uid()+'/policy',
                                                  {'policy':'single'},self.nodes[1]['cfg']['token']))
        plan=self.global_client.request('POST','uploads',{'idempotency_key':'scope_upload_req','logical_path':'scope.bin',
            'size':len(self.data),'sha256':self.sha,'policy':'replicated_2'})
        target=plan['target'];client=StorageClient(target['origin'],target['pin'],target['grant'],target['volume_id'])
        self.assert_status(403,lambda:client.initiate('unauthorized_key','outside',0,hashlib.sha256(b'').hexdigest()))
        self.assert_status(403,lambda:client.json('GET','files'))
        self.assert_status(400,lambda:self.global_client.request('POST','uploads/'+plan['job_id']+'/complete',
            {'session_id':uid(),'local_file_id':uid(),'physically_verified':True}))
        self.global_client.request('POST','uploads/'+plan['job_id']+'/complete',{'session_id':uid(),'local_file_id':uid()})
        self.assertEqual(self.service.catalog.file(plan['file']['file']['file_id'])['verified_replicas'],0)
        self.reg.revoke(target['node_id'])
        self.assert_status(403,lambda:client.initiate(plan['idempotency_key'],plan['local_logical_path'],len(self.data),self.sha))
        self.assert_status(403,lambda:request_json(self.origin,self.pin,'GET','/catalog/v1/metadata/snapshot?node_id='+target['node_id'],
                                                  token=self.node_for(target['node_id'])['cfg']['token']))

    def test_insufficient_capacity_protected_node_and_manifest_mismatch(self):
        file_id=self.upload_global('single')
        replica=self.service.catalog.file(file_id)['replicas'][0]
        holder=self.node_for(replica['node_id'])
        with holder['runtime'].engine.manifest.connect() as db:
            db.execute('UPDATE files SET size=size+1 WHERE file_id=?',(replica['local_file_id'],))
        self.service.reconcile()
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],0)
        self.assertTrue(self.physical(replica).exists())
        for node in self.nodes:
            with self.reg.connect() as db:
                db.execute('UPDATE nodes SET profile=? WHERE node_id=?',(json.dumps({'protected':True}),node['cfg']['node_id']))
        self.assert_status(507,lambda:self.global_client.upload(io.BytesIO(self.data),'no-target.bin','no_capacity_key'))
        self.assert_status(403,lambda:self.global_client.request('POST','nodes/register',{'node_id':self.nodes[0]['cfg']['node_id'],
            'origin':'https://127.0.0.1:'+str(self.nodes[0]['port']),'pin':self.nodes[0]['pin'],'device_id':'M51-protected',
            'volume_ids':[self.nodes[0]['volume']]}))

    def test_mid_stream_disconnect_retries_same_session_without_publishing_partial_copy(self):
        from asc.catalog.transport import RelayReader
        import time
        file_id=self.upload_global()
        original=RelayReader.read
        def disconnect(reader,size):
            if reader.purpose=='transfer' and reader.count>=65536:
                deadline=time.monotonic()+5
                while True:
                    with self.reg.connect() as db:
                        active=dict(db.execute("SELECT * FROM catalog_jobs WHERE state='RUNNING' AND kind='COPY'").fetchone())
                    target=self.node_for(active['target_node_id'])
                    with target['runtime'].engine.manifest.connect() as db:
                        state=db.execute('SELECT state FROM uploads WHERE file_id=?',(active['target_local_file_id'],)).fetchone()[0]
                    if state=='WRITING':break
                    if time.monotonic()>=deadline:self.fail('target did not enter WRITING before the injected disconnect')
                    time.sleep(0.01)
                reader.stream.close()
                raise ConnectionResetError('injected mid-stream disconnect')
            return original(reader,size)
        with mock.patch.object(RelayReader,'read',disconnect):
            job=self.service.run_one()
        self.assertEqual(job['state'],'RETRY')
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],1)
        target=self.node_for(job['target_node_id'])
        deadline=time.monotonic()+5
        while True:
            with target['runtime'].engine.manifest.connect() as db:
                row=db.execute('SELECT state FROM uploads WHERE file_id=?',(job['target_local_file_id'],)).fetchone()
            if row['state']=='INTERRUPTED' or time.monotonic()>=deadline:break
            time.sleep(0.01)
        self.assertEqual(row['state'],'INTERRUPTED')
        with self.reg.connect() as db:db.execute('UPDATE catalog_jobs SET next_attempt_at=0 WHERE job_id=?',(job['job_id'],))
        retried=self.service.run_one()
        self.assertEqual(retried['job_id'],job['job_id']);self.assertEqual(retried['target_local_file_id'],job['target_local_file_id'])
        self.assertEqual(retried['state'],'COMPLETED')
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],2)

    def test_target_offline_after_commit_before_confirmation_keeps_bytes_for_retry(self):
        file_id=self.upload_global()
        stopped=[]
        def offline(phase,job):
            target=self.node_for(job['target_node_id'])
            target['runtime'].__exit__(None,None,None);stopped.append(target)
            raise ConnectionResetError('target offline before confirmation')
        self.service.fault_hook=offline
        job=self.service.run_one()
        self.assertEqual(job['state'],'RETRY');self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],1)
        target=stopped[0]
        path=self.base/str(self.nodes.index(target))/'data'/'objects'/(job['target_local_file_id']+'.blob')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),self.sha)
        target['runtime']=StorageRuntime(target['private'],target['cfg']).__enter__()
        self.service.fault_hook=None
        with self.reg.connect() as db:db.execute('UPDATE catalog_jobs SET next_attempt_at=0 WHERE job_id=?',(job['job_id'],))
        result=self.service.run_one()
        self.assertEqual(result['state'],'COMPLETED');self.assertEqual(result['target_local_file_id'],job['target_local_file_id'])

    def test_quota_shortfall_reports_under_replication_without_fake_protection(self):
        file_id=self.upload_global('single')
        holder=self.service.catalog.file(file_id)['replicas'][0]['node_id']
        for node in self.nodes:
            if node['cfg']['node_id']!=holder:
                with node['runtime'].engine.manifest.connect() as db:
                    db.execute('UPDATE volumes SET quota=?',(len(self.data),))
        entry=self.global_client.request('POST','files/'+file_id+'/policy',{'policy':'replicated_3'})
        self.assertEqual(entry['desired_replicas'],3)
        self.assertEqual(entry['verified_replicas'],1)
        self.assertEqual(entry['protection'],'DEGRADED')
        self.assertIsNone(self.service.run_one())
        self.assertEqual(len(self.service.catalog.file(file_id)['replicas']),1)

    def test_lost_upload_ack_is_recovered_from_matching_verified_local_manifest(self):
        plan=self.global_client.request('POST','uploads',{'idempotency_key':'lost_ack_request','logical_path':'lost-ack.bin',
            'size':len(self.data),'sha256':self.sha,'policy':'replicated_2'})
        target=plan['target'];client=StorageClient(target['origin'],target['pin'],target['grant'],target['volume_id'])
        session=client.initiate(plan['idempotency_key'],plan['local_logical_path'],len(self.data),self.sha)
        client.upload(session['session_id'],io.BytesIO(self.data),len(self.data));client.commit(session['session_id'])
        file_id=plan['file']['file']['file_id']
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],0)
        report=self.service.reconcile()
        self.assertIn(plan['job_id'],report['recovered_uploads'])
        self.drain()
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],2)

    def test_owner_cli_upload_download_and_offline_metadata_lookup(self):
        from asc import identity
        from asc.identity import save_private
        home=self.base/'controller'
        save_private(home/'controller.json',{'config_version':1,'admin_token':self.admin,
            'listen_port':self.server.server_address[1],'cluster_id':'test-cluster'})
        source=self.base/'owner-source.bin';source.write_bytes(self.data)
        text=io.StringIO()
        with mock.patch.object(cli,'HOME',home),mock.patch.object(identity,'HOME',home),mock.patch.object(cli,'inspect',return_value={'protected':False}),mock.patch('sys.argv',['asc','catalog-upload',str(source),'cli-global.bin','--key','cli_global_request']),contextlib.redirect_stdout(text):
            cli.main()
        result=json.loads(text.getvalue());file_id=result['file']['file']['file_id']
        self.drain();output=self.base/'owner-download.bin'
        with mock.patch.object(cli,'HOME',home),mock.patch.object(identity,'HOME',home),mock.patch.object(cli,'inspect',return_value={'protected':False}),mock.patch('sys.argv',['asc','catalog-download',file_id,str(output)]),contextlib.redirect_stdout(io.StringIO()):
            cli.main()
        self.assertEqual(output.read_bytes(),self.data)
        node=self.nodes[0];synchronize(node['private'],node['cfg'])
        captured=io.StringIO()
        with mock.patch.object(cli,'HOME',node['private']),mock.patch.object(identity,'HOME',node['private']),mock.patch('sys.argv',['asc','catalog-local-file',file_id]),contextlib.redirect_stdout(captured):
            cli.main()
        self.assertTrue(json.loads(captured.getvalue())['metadata']['read_only'])

    def test_background_worker_automatically_replicates_and_agent_syncs_metadata(self):
        import time
        self.service.close()
        self.service=CatalogService(self.reg).start(background=True)
        self.server.catalog=self.service
        result=self.global_client.upload(io.BytesIO(self.data),'automatic.bin','automatic_upload')
        file_id=result['file']['file']['file_id']
        deadline=time.monotonic()+15
        while self.service.catalog.file(file_id)['verified_replicas']<2 and time.monotonic()<deadline:
            time.sleep(0.05)
        self.assertEqual(self.service.catalog.file(file_id)['verified_replicas'],2)
        node=self.nodes[1]
        with mock.patch.object(cli,'HOME',node['private']),mock.patch.object(cli,'inspect',return_value={'profile_version':1,'model':node['name'],'protected':False,'simulation':True}):
            cli.agent_once(node['cfg'],storage_engine=node['runtime'].engine)
        cache=MetadataReplica(node['private']/'catalog-metadata.sqlite3','test-cluster',read_only=True)
        self.assertEqual(len(cache.file(file_id)['entry']['replicas']),2)

    def test_removed_volume_repairs_to_spare_node_without_deleting_old_medium(self):
        file_id=self.upload_global();self.drain()
        offline=self.service.catalog.file(file_id)['replicas'][0]
        node=self.node_for(offline['node_id']);index=self.nodes.index(node)
        self.assertTrue(node['runtime'].engine._transfer.acquire(timeout=5))
        node['runtime'].engine._transfer.release()
        root=self.base/str(index)/'data';removed=root.with_name('removed-medium')
        root.rename(removed)
        try:
            self.service.reconcile()
            self.assertEqual(self.service.catalog.file(file_id)['available_replicas'],1)
            self.drain()
            self.assertEqual(self.service.catalog.file(file_id)['available_replicas'],2)
            self.assertTrue((removed/'objects'/(offline['local_file_id']+'.blob')).exists())
        finally:removed.rename(root)

    def test_metadata_only_approval_and_gap_resync_are_safe(self):
        node=self.nodes[2]
        self.global_client.request('POST','nodes/register',{'node_id':node['cfg']['node_id'],'device_id':node['name'],
                                                           'metadata_allowed':True,'storage_allowed':False})
        file_id=self.upload_global()
        synchronize(node['private'],node['cfg'])
        self.drain()
        with self.reg.connect() as db:db.execute('DELETE FROM catalog_events')
        status=synchronize(node['private'],node['cfg'])
        self.assertEqual(status['lag'],0)
        cache=MetadataReplica(node['private']/'catalog-metadata.sqlite3','test-cluster',read_only=True)
        self.assertEqual(len(cache.file(file_id)['entry']['replicas']),2)
        self.assertNotIn(node['cfg']['node_id'],[r['node_id'] for r in self.service.catalog.file(file_id)['replicas']])
        self.assert_status(400,lambda:self.global_client.request('POST','uploads',{'idempotency_key':'traversal_catalog',
            'logical_path':'../escape','size':0,'sha256':hashlib.sha256(b'').hexdigest(),'policy':'single'}))

    def test_legacy_scope_negotiation_keeps_whole_volume_grants_but_never_job_grants(self):
        from asc.storage import http as node_http
        actual=node_http.request_json
        def old_schema(origin,pin,method,path,obj=None,token=None):
            if path=='/api/v1/storage/authorize' and obj and 'scope' in obj:
                raise ClientError('old schema',400,'bad_request')
            return actual(origin,pin,method,path,obj,token)
        plan=self.service.upload_plan({'idempotency_key':'no_scope_job_grant','logical_path':'no-scope.bin',
            'size':len(self.data),'sha256':self.sha,'policy':'single'})
        with mock.patch.object(node_http,'request_json',side_effect=old_schema):
            self.assertEqual(self.client.json('GET','files')['files'],[])
            target=plan['target'];scoped=StorageClient(target['origin'],target['pin'],target['grant'],target['volume_id'])
            self.assert_status(403,lambda:scoped.initiate(plan['idempotency_key'],plan['local_logical_path'],len(self.data),self.sha))
