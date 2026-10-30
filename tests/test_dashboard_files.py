"""Actual TLS file/version/job UI API; metadata-only plans are never protected."""
import hashlib
import json
import secrets
import unittest
from asc.client import request_json
from asc.storage.client import StorageClient
from tests import test_demo_dashboard as fixture


def query(**changes):
    return dict(browse_api_version=1, offset=0, search='', folder='', recursive=True,
                sort='name', versions='all') | changes


class FileManagerTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.DashboardAPITests(); self.addCleanup(self.f.doCleanups); self.f.setUp()

    def page(self, **changes):
        status, _, result = self.f.http('POST', '/api/files/query', query(**changes))
        self.assertEqual(status, 200, result)
        return result

    def upload(self, data, version, key, path='versions/thử.txt'):
        obj = dict(logical_path=path, version=version, idempotency_key=key,
                   size=len(data), sha256=hashlib.sha256(data).hexdigest())
        def prepare():
            status, _, plan = self.f.http('POST', '/api/uploads', obj)
            if status == 409 and plan.get('error') == 'transfer_busy':
                return False  # Same intent, real worker finishes its current proof.
            self.assertEqual(status, 200, plan)
            return plan
        plan = self.f.wait_for(prepare)
        if not plan['completed']:
            status, _, reply = self.f.http('PUT', '/api/uploads/'+plan['transfer_id'], body=data,
                headers={'Content-Type':'application/octet-stream'})
            self.assertIn(status, (200,202), reply)
        file_id = plan['file']['file_id']
        return self.f.wait_for(lambda: self.f.http('GET', '/api/files/'+file_id)[2]['protected'] and
                               self.f.http('GET', '/api/files/'+file_id)[2])

    def test_explicit_versions_real_two_replica_bytes_restart_and_idempotency(self):
        first = self.upload(b'first immutable bytes', 1, 'first_version_key')
        second = self.upload(b'new content does not replace old bytes', 2, 'second_version_key')
        again = self.upload(b'new content does not replace old bytes', 2, 'second_version_key')
        self.assertEqual(again['file_id'], second['file_id'])
        self.assertNotEqual(first['file_id'], second['file_id'])
        self.assertEqual([x['version'] for x in self.page(history_file_id=first['file_id'])['entries']], [2,1])
        self.assertEqual([x['file_id'] for x in self.page(versions='latest')['entries']], [second['file_id']])
        collision = dict(logical_path=first['logical_path'], version=1, idempotency_key='collision_upload_key',size=3,sha256=hashlib.sha256(b'new').hexdigest())
        self.assertEqual(self.f.http('POST','/api/uploads',collision)[0],409)
        self.f.stop(self.f.controller_process)
        self.f.controller_process=self.f.start(self.f.controller,'run-controller'); self.f.login()
        for file, data in ((first,b'first immutable bytes'),(second,b'new content does not replace old bytes')):
            status, headers, body=self.f.http('GET','/api/files/'+file['file_id']+'/content',json_response=False)
            self.assertEqual((status,body),(200,data)); self.assertEqual(headers['X-ASC-SHA256'],hashlib.sha256(body).hexdigest())

    def test_canonical_pending_plans_pagination_logical_folders_literal_unicode_search(self):
        # Real canonical plans, deliberately WITHOUT upload/physical proof. Stay
        # within the unchanged Core256 metadata bound; never fake replica success.
        ids=[]
        for i in range(53):
            plan=request_json(self.f.origin,self.f.pin,'POST','/catalog/v1/uploads',dict(
                logical_path=f'documents/sub/item-{i:03d}.txt',version=1,idempotency_key='listing_'+str(i).zfill(8),
                size=4,sha256=hashlib.sha256(b'data').hexdigest(),policy='replicated_2'),self.f.admin())
            ids.append(plan['file']['file']['file_id'])
        first=self.page(); self.assertEqual((first['total'],len(first['entries']),first['next_offset']),(53,50,50))
        tail=self.page(offset=50);self.assertEqual((len(tail['entries']),tail['next_offset']),(3,None))
        self.assertEqual(set(ids),{x['file_id'] for x in first['entries']+tail['entries']})
        self.assertTrue(all(not x['protected'] and x['verified_replicas']==0 for x in first['entries']))
        self.assertEqual(self.page(recursive=False)['entries'],[dict(kind='folder',logical_path='documents')])
        self.assertEqual(self.page(folder='documents',recursive=False)['entries'],[dict(kind='folder',logical_path='documents/sub')])
        self.assertEqual(self.page(folder='documents/sub',recursive=False)['total'],53)
        self.assertEqual(self.page(search='ITEM-052')['entries'][0]['file_id'],ids[-1])
        self.assertEqual(self.page(search='%')['total'],0)  # Literal, not LIKE wildcard.
        self.upload(b'unicode data',1,'unicode_search_key',path='Tài-liệu/ĐIỆN.txt')
        self.assertEqual(self.page(search='điện')['total'],1)

    def test_strict_query_version_validation_sessions_roles_no_grants_or_paths(self):
        for changes in ({'offset':True},{'offset':-1},{'offset':10001},{'folder':'../escape'},
                        {'folder':'/etc'},{'recursive':1},{'sort':'shell'},{'search':'x'*129},
                        {'search':'\n'},{'browse_api_version':True},{'volumes':'forbidden'}, {'history_file_id':'../x'}):
            self.assertEqual(self.f.http('POST','/api/files/query',query(**changes))[0],400,changes)
        self.assertEqual(self.f.http('POST','/api/files/query',query(),authenticated=False)[0],401)
        self.assertEqual(self.f.http('POST','/api/files/query',query(),headers={'Origin':'https://evil.invalid'})[0],403)
        self.assertEqual(self.f.http('GET','/api/files/query?offset=0')[0],400)
        base=dict(logical_path='new.txt',size=0,sha256=hashlib.sha256(b'').hexdigest(),idempotency_key='strict_upload_key')
        for version in (True,0,1000001,'2',None):
            self.assertEqual(self.f.http('POST','/api/uploads',base|{'version':version})[0],400)
        password=secrets.token_urlsafe(24)
        self.assertEqual(self.f.http('POST','/api/accounts',dict(username='primary',password=password,role='owner'))[0],201)
        self.assertEqual(self.f.http('POST','/api/accounts',dict(username='reader',password=password,role='viewer'))[0],201)
        status,headers,login=self.f.http('POST','/api/login',dict(username='reader',password=password),authenticated=False)
        self.assertEqual(status,200)
        self.f.cookie=headers['Set-Cookie'].split(';')[0];self.f.csrf=login['csrf']
        self.assertEqual(self.f.http('POST','/api/files/query',query())[0],200)
        self.assertEqual(self.f.http('POST','/api/jobs/query',{'offset':0})[0],200)
        self.assertEqual(self.f.http('POST','/api/uploads',base)[0],403)
        self.assertEqual(self.f.http('POST','/api/jobs/00000000-0000-0000-0000-000000000000/retry',{})[0],403)
        serialized=json.dumps(self.page())
        for secret in (self.f.admin(),self.f.nodes[0]['cfg']['token'],str(self.f.controller)):
            self.assertNotIn(secret,serialized)

    def test_premature_real_storage_ack_fails_proof_owner_retry_then_actual_bytes_recover(self):
        plan=request_json(self.f.origin,self.f.pin,'POST','/catalog/v1/uploads',dict(
            logical_path='retry/real.bin',size=len(self.f.data),sha256=hashlib.sha256(self.f.data).hexdigest(),
            version=1,idempotency_key='retry_real_storage',policy='replicated_2'),self.f.admin())
        target=plan['target']; storage=StorageClient(target['origin'],target['pin'],target['grant'],target['volume_id'])
        session=storage.initiate(plan['idempotency_key'],plan['local_logical_path'],len(self.f.data),hashlib.sha256(self.f.data).hexdigest())
        # Actual staging exists, but no body or commit. Canonical readback must
        # refuse this premature ACK, preserving durable RETRY and zero replicas.
        ack=request_json(self.f.origin,self.f.pin,'POST','/catalog/v1/uploads/'+plan['job_id']+'/complete',
            dict(session_id=session['session_id'],local_file_id=session['file_id']),self.f.admin())
        self.assertNotEqual(ack['job_state'],'COMPLETED');self.assertEqual(ack['file']['verified_replicas'],0)
        self.assertEqual(self.f.http('POST','/api/jobs/query',{'offset':0})[0],200)
        path='/api/jobs/'+plan['job_id']
        status,_,detail=self.f.http('GET',path);self.assertEqual(status,200);self.assertTrue(detail['job']['retryable'])
        for forbidden in ('grant','run_token','target_generation','source_generation','session_id','admin_token'):
            self.assertNotIn(forbidden,json.dumps(detail))
        self.assertEqual(self.f.http('POST',path+'/retry',{},authenticated=False)[0],401)
        self.assertEqual(self.f.http('POST',path+'/retry',{})[0],200)
        entry=self.upload(self.f.data,1,'retry_real_storage',path='retry/real.bin')
        self.assertTrue(entry['protected'])
        self.assertEqual(self.f.http('POST',path+'/retry',{})[0],409)
        status,_,detail=self.f.http('GET',path)
        self.assertEqual(detail['job']['state'],'COMPLETED');self.assertFalse(detail['job']['retryable'])
        status,_,raw=self.f.http('GET','/api/files/'+entry['file_id']+'/content',json_response=False)
        self.assertEqual((status,raw),(200,self.f.data))


if __name__=='__main__':unittest.main()
