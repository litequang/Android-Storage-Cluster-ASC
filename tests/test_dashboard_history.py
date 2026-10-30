"""Real TLS/bytes single-writer snapshots and non-destructive immutable restore."""
import hashlib
import http.client
import json
import secrets
import time
import unittest
import uuid
from tests import test_demo_dashboard as fixture
from tests import test_dashboard_files as file_fixture


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.DashboardAPITests();self.addCleanup(self.f.doCleanups);self.f.setUp()

    def view(self):
        status,_,value=self.f.http('GET','/api/history');self.assertEqual(status,200,value);return value

    def snapshot(self,prefix='',request_id=None):
        obj=dict(history_api_version=1,request_id=request_id or str(uuid.uuid4()),label='Snapshot thử nghiệm',prefix=prefix)
        status,_,result=self.f.http('POST','/api/history/snapshots',obj);self.assertEqual(status,201,result)
        return result,obj

    def step(self,kind,item):
        status,_,result=self.f.http('POST','/api/history/'+kind+'/'+item+'/step',{})
        self.assertEqual(status,200,result);return result

    def restore(self,file,snapshot_id=None,request_id=None):
        obj=dict(history_api_version=1,request_id=request_id or str(uuid.uuid4()),file_id=file['file_id'],snapshot_id=snapshot_id)
        status,_,result=self.f.http('POST','/api/history/restores',obj);self.assertEqual(status,201,result)
        return result,obj

    def upload(self,data,version=1,key=None,path='history/file.bin'):
        helper=file_fixture.FileManagerTests();helper.f=self.f
        return helper.upload(data,version,key or str(uuid.uuid4()),path)

    def test_snapshot_exact_metadata_all_versions_real_sha_then_restore_new_version(self):
        first=self.upload(b'original bytes',1);second=self.upload(b'newer bytes',2)
        snap,_=self.snapshot('history');sid=snap['snapshot_id'];before=self.view()['snapshots'][sid]
        self.assertEqual(before['state'],'UNVERIFIED');self.assertEqual(before['cursor'],0)
        manifest=before['manifest'];self.assertNotIn('source_term',manifest);self.assertNotIn('source_index',manifest)
        self.assertEqual([f['version'] for f in manifest['files']],[1,2]);self.assertEqual(before['proofs'],[])
        self.assertEqual(self.step('snapshots',sid)['state'],'VERIFYING')
        self.assertEqual(self.step('snapshots',sid)['state'],'VERIFIED')
        verified=self.view()['snapshots'][sid]
        self.assertEqual(verified['manifest'],manifest)
        self.assertTrue(all(len(set(p['domains']))==2 for p in verified['proofs']))
        self.assertTrue(self.step('snapshots',sid)['historical'])
        restore,_=self.restore(first,sid);rid=restore['restore_id']
        def done():return self.step('restores',rid)['state']=='COMPLETED'
        self.f.wait_for(done);job=self.view()['restores'][rid]
        self.assertEqual(job['target_version'],3);self.assertNotIn(job['target_file_id'],(first['file_id'],second['file_id']))
        for file_id,data in ((first['file_id'],b'original bytes'),(second['file_id'],b'newer bytes'),(job['target_file_id'],b'original bytes')):
            status,headers,body=self.f.http('GET','/api/files/'+file_id+'/content',json_response=False)
            self.assertEqual((status,body),(200,data));self.assertEqual(headers['X-ASC-SHA256'],hashlib.sha256(body).hexdigest())
        for secret in (self.f.admin(),self.f.nodes[0]['cfg']['token'],str(self.f.controller)):
            self.assertNotIn(secret,json.dumps(self.view()))

    def test_actual_lost_successful_tls_ack_restart_resume_and_identity_preservation(self):
        file=self.upload(self.f.data);snap,obj=self.snapshot();sid=snap['snapshot_id']
        self.assertEqual(self.f.http('POST','/api/history/snapshots',obj)[2]['snapshot_id'],sid)
        self.assertTrue(self.f.http('POST','/api/history/snapshots',obj)[2]['replayed'])
        self.assertEqual(self.f.http('POST','/api/history/snapshots',obj|{'label':'changed'})[0],409)
        self.assertEqual(self.step('snapshots',sid)['state'],'VERIFIED')
        restore,request=self.restore(file,sid);rid=restore['restore_id']
        identity={str(p):p.read_bytes() for p in [self.f.controller/'controller/controller.json',self.f.controller/'controller/server.crt',*[n['root']/'node/node.json' for n in self.f.nodes]]}
        # Send a genuine TLS step, deliberately discard its successful response.
        connection=http.client.HTTPSConnection('127.0.0.1',self.f.dashboard_port,context=self.f.context,timeout=20)
        connection.request('POST','/api/history/restores/'+rid+'/step',body=b'{}',headers={
            'Origin':self.f.browser_origin,'Cookie':self.f.cookie,'X-ASC-CSRF':self.f.csrf,'Content-Type':'application/json'})
        connection.close()
        self.f.wait_for(lambda:self.view()['restores'][rid]['state'] in ('COMPLETED','VERIFYING'))
        self.f.stop(self.f.controller_process);self.f.controller_process=self.f.start(self.f.controller,'run-controller');self.f.login()
        self.assertEqual(self.f.http('POST','/api/history/restores',request)[2]['restore_id'],rid)
        self.f.wait_for(lambda:self.step('restores',rid)['state']=='COMPLETED')
        job=self.view()['restores'][rid];self.assertEqual(job['target_version'],2)
        self.assertEqual(len(self.view()['restores']),1)
        from pathlib import Path
        self.assertEqual(identity,{name:Path(name).read_bytes() for name in identity})
        self.assertEqual(self.f.http('GET','/api/files/'+job['target_file_id']+'/content',json_response=False)[2],self.f.data)

    def test_missing_or_corrupt_copy_never_verifies_snapshot_and_retains_all_objects(self):
        file=self.upload(self.f.data);snap,_=self.snapshot();sid=snap['snapshot_id']
        before={str(p):p.read_bytes() for n in self.f.nodes for p in (n['root']/'node/data/objects').glob('*.blob')}
        self.assertGreaterEqual(len(before),2)
        self.f.stop(self.f.nodes[0]['process'])
        self.assertEqual(self.step('snapshots',sid)['state'],'VERIFYING');self.assertIsNone(self.view()['snapshots'][sid]['verified_at'])
        self.assertEqual(self.f.http('POST','/api/history/restores',dict(history_api_version=1,request_id=str(uuid.uuid4()),file_id=file['file_id'],snapshot_id=sid))[0],409)
        from pathlib import Path
        self.assertEqual(before,{name:Path(name).read_bytes() for name in before})
        self.f.nodes[0]['process']=self.f.start(self.f.nodes[0]['root'],'run-node')
        self.f.wait_for(lambda:self.step('snapshots',sid)['state']=='VERIFIED')

    def test_pending_upload_never_becomes_snapshot_verified_and_source_change_keeps_manifest(self):
        first=self.upload(b'initial');snap,_=self.snapshot();sid=snap['snapshot_id'];manifest=self.view()['snapshots'][sid]['manifest']
        self.upload(b'later',2)
        self.assertEqual(self.step('snapshots',sid)['state'],'VERIFIED')
        self.assertEqual(self.view()['snapshots'][sid]['manifest'],manifest)
        self.assertEqual(manifest['files'][0]['file_id'],first['file_id'])
        self.f.prepare(key='pending_history_plan',name='pending/missing.bin')
        pending,_=self.snapshot('pending');pid=pending['snapshot_id']
        result=self.step('snapshots',pid);self.assertEqual((result['state'],result['cursor']),('VERIFYING',0))
        self.assertEqual(self.view()['snapshots'][pid]['proofs'],[])

    def test_private_progress_corruption_links_missing_witness_and_no_reset(self):
        self.upload(b'private state');self.snapshot()
        path=self.f.controller/'dashboard/history.json';witness=self.f.controller/'dashboard/history-required.json'
        original=path.read_bytes();required=witness.read_bytes()
        self.assertEqual(path.stat().st_mode&0o777,0o600)
        for mutation in (b'{}',original.replace(b'"format":1',b'"format":2',1),original.replace(b'"manifest_sha256":"',b'"manifest_sha256":"0',1)):
            path.write_bytes(mutation);self.assertEqual(self.f.http('GET','/api/history')[0],503);self.assertEqual(path.read_bytes(),mutation)
        path.write_bytes(original);path.chmod(0o644);self.assertEqual(self.f.http('GET','/api/history')[0],503);path.chmod(0o600)
        held=path.with_suffix('.held');path.rename(held);path.symlink_to(held)
        self.assertEqual(self.f.http('GET','/api/history')[0],503);path.unlink();self.assertEqual(self.f.http('GET','/api/history')[0],503);held.rename(path)
        witness.rename(witness.with_suffix('.held'));self.assertEqual(self.f.http('GET','/api/history')[0],503)
        witness.with_suffix('.held').rename(witness);self.assertEqual(witness.read_bytes(),required)
        self.assertEqual(self.f.http('GET','/api/history')[0],200)

    def test_owner_csrf_viewer_read_only_confirmation_validation_and_no_gc(self):
        file=self.upload(b'role protected');snap,obj=self.snapshot();sid=snap['snapshot_id']
        self.assertEqual(self.f.http('POST','/api/history/snapshots',obj,authenticated=False)[0],401)
        self.assertEqual(self.f.http('POST','/api/history/snapshots',obj,headers={'Origin':'https://evil.invalid'})[0],403)
        self.assertEqual(self.f.http('POST','/api/history/snapshots',obj|{'prefix':'../escape','request_id':str(uuid.uuid4())})[0],400)
        self.assertEqual(self.f.http('POST','/api/history/snapshots/'+sid+'/step',{'shell':'forbidden'})[0],400)
        password=secrets.token_urlsafe(24)
        for name,role in (('primary','owner'),('reader','viewer')):
            self.assertEqual(self.f.http('POST','/api/accounts',dict(username=name,role=role,password=password))[0],201)
        status,headers,reply=self.f.http('POST','/api/login',dict(username='reader',password=password),authenticated=False)
        self.assertEqual(status,200);self.f.cookie=headers['Set-Cookie'].split(';')[0];self.f.csrf=reply['csrf']
        self.assertEqual(self.f.http('GET','/api/history')[0],200)
        for path,body in (('/api/history/snapshots',obj),('/api/history/snapshots/'+sid+'/step',{}),
                          ('/api/history/restores',dict(history_api_version=1,request_id=str(uuid.uuid4()),file_id=file['file_id'],snapshot_id=None))):
            self.assertEqual(self.f.http('POST',path,body)[0],403)
        caps=self.f.http('GET','/api/capabilities')[2]
        self.assertTrue(caps['snapshot_read']);self.assertFalse(caps['snapshot_restore']);self.assertFalse(caps['physical_gc']);self.assertFalse(caps['recovery_writer'])

    def test_concurrent_version_collision_blocks_without_overwrite_or_automatic_bump(self):
        first=self.upload(b'old protected content',1)
        restore,_=self.restore(first);rid=restore['restore_id']
        concurrent=self.upload(b'concurrent owner content',2)
        result=self.step('restores',rid)
        self.assertEqual((result['state'],result['error'],result['target_version']),('BLOCKED','version_conflict',2))
        self.assertEqual(self.step('restores',rid)['state'],'BLOCKED')
        for file,data in ((first,b'old protected content'),(concurrent,b'concurrent owner content')):
            self.assertEqual(self.f.http('GET','/api/files/'+file['file_id']+'/content',json_response=False)[2],data)
        reviewed,_=self.restore(first)
        self.f.wait_for(lambda:self.step('restores',reviewed['restore_id'])['state']=='COMPLETED')
        self.assertEqual(self.view()['restores'][reviewed['restore_id']]['target_version'],3)

    def test_actual_corrupt_replica_refuses_snapshot_and_preserves_last_readable_copy(self):
        file=self.upload(self.f.data);snap,_=self.snapshot();sid=snap['snapshot_id']
        corrupt=next((self.f.nodes[0]['root']/'node/data/objects').glob('*.blob'))
        damaged=b'controlled synthetic corruption';corrupt.write_bytes(damaged)
        result=self.step('snapshots',sid)
        self.assertEqual((result['state'],result['cursor']),('VERIFYING',0))
        self.assertEqual(self.view()['snapshots'][sid]['proofs'],[])
        self.assertEqual(corrupt.read_bytes(),damaged)  # Corrupt retained body is never deleted or replaced.
        status,headers,body=self.f.http('GET','/api/files/'+file['file_id']+'/content',json_response=False)
        self.assertEqual((status,body),(200,self.f.data));self.assertEqual(headers['X-ASC-SHA256'],hashlib.sha256(body).hexdigest())


if __name__=='__main__':unittest.main()
