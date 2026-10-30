"""Private credential persistence and real owner/viewer HTTPS authorization."""
from contextlib import closing
import hashlib
from http.cookies import SimpleCookie
import json
from pathlib import Path
import secrets
import sqlite3
import tempfile
import unittest
import uuid
from unittest.mock import patch

from asc.demo.dashboard.accounts import Accounts, AccountError, ITERATIONS
from asc.demo.dashboard.auth import Sessions, COOKIE
from tests import test_demo_dashboard as fixture


class AccountStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.asc-accounts-',dir=Path.home());self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'dashboard').mkdir(mode=0o700)
        self.cluster=str(uuid.uuid4());self.accounts=Accounts(self.root,self.cluster);self.password=secrets.token_urlsafe(24)

    def test_no_default_credentials_standard_kdf_private_file_and_restart(self):
        self.assertFalse(self.accounts.path.exists());self.assertFalse(self.accounts.list()['password_enabled'])
        with self.assertRaises(AccountError):self.accounts.create(dict(username='reader',password=self.password,role='viewer'))
        self.assertFalse(self.accounts.path.exists())
        owner=self.accounts.create(dict(username='primary',password=self.password,role='owner'))
        raw=self.accounts.path.read_bytes();self.assertNotIn(self.password.encode(),raw)
        self.assertEqual(self.accounts.path.stat().st_mode&0o777,0o600)
        record=json.loads(raw);self.assertEqual(record['iterations'],600000)
        row=record['accounts']['primary']
        self.assertEqual(row['password_hash'],hashlib.pbkdf2_hmac('sha256',self.password.encode(),bytes.fromhex(row['salt']),ITERATIONS).hex())
        resumed=Accounts(self.root,self.cluster)
        self.assertEqual(resumed.authenticate('primary',self.password),owner)
        self.assertIsNone(resumed.authenticate('primary',secrets.token_urlsafe(24)))
        self.assertIsNone(resumed.authenticate('unknown',self.password))
        self.assertNotIn('password_hash',json.dumps(resumed.list()));self.assertNotIn('salt',json.dumps(resumed.list()))

    def test_stale_changes_last_owner_and_no_auto_identity_replacement(self):
        original=self.accounts.create(dict(username='primary',password=self.password,role='owner'))
        before=self.accounts.path.read_bytes()
        for delete,role in ((True,'owner'),(False,'viewer')):
            with self.assertRaises(AccountError):self.accounts.change('primary',dict(expected_generation=1,role=role,password='',delete=delete))
        with self.assertRaises(AccountError):self.accounts.change('primary',dict(expected_generation=999,role='owner',password='',delete=False))
        self.assertEqual(self.accounts.path.read_bytes(),before)
        newer=secrets.token_urlsafe(24)
        self.accounts.change('primary',dict(expected_generation=1,role='owner',password=newer,delete=False))
        current=self.accounts.authenticate('primary',newer)
        self.assertEqual(current['account_id'],original['account_id']);self.assertEqual(current['generation'],2)
        self.assertIsNone(self.accounts.authenticate('primary',self.password))
        self.accounts.path.unlink()  # Synthetic credential loss; read never recreates a file/account.
        self.assertIsNone(Accounts(self.root,self.cluster).authenticate('primary',newer));self.assertFalse(self.accounts.path.exists())

    def test_corruption_permissions_links_and_atomic_write_failure_refuse(self):
        self.accounts.create(dict(username='primary',password=self.password,role='owner'));before=self.accounts.path.read_bytes()
        with patch('asc.bridge.private.os.replace',side_effect=OSError('synthetic publication failure')):
            with self.assertRaises(OSError):self.accounts.change('primary',dict(expected_generation=1,role='owner',password=secrets.token_urlsafe(24),delete=False))
        self.assertEqual(self.accounts.path.read_bytes(),before)
        self.assertIsNotNone(Accounts(self.root,self.cluster).authenticate('primary',self.password))
        with self.assertRaises(AccountError):Accounts(self.root,str(uuid.uuid4()))
        self.accounts.path.chmod(0o644)
        with self.assertRaises(AccountError):Accounts(self.root,self.cluster)
        self.accounts.path.chmod(0o600)
        self.accounts.path.write_text('{corrupt')
        with self.assertRaises(AccountError):Accounts(self.root,self.cluster)
        self.assertEqual(self.accounts.path.read_text(),'{corrupt')
        self.accounts.path.unlink();outside=self.root/'outside';outside.write_bytes(before);outside.chmod(0o600)
        self.accounts.path.symlink_to(outside)
        with self.assertRaises(AccountError):Accounts(self.root,self.cluster)
        self.assertEqual(outside.read_bytes(),before)

    def test_user_limit_and_password_sessions_share_original_global_bound(self):
        owner=self.accounts.create(dict(username='primary',password=self.password,role='owner'))
        for i in range(7):self.accounts.create(dict(username='reader'+str(i),password=secrets.token_urlsafe(20),role='viewer'))
        with self.assertRaises(AccountError):self.accounts.create(dict(username='too_many',password=self.password,role='viewer'))
        sessions=Sessions();self.assertIsNotNone(sessions.login(sessions.issue()))
        cookies=[]
        for i in range(7):cookies.append(sessions.create(owner)[0])
        self.assertIsNone(sessions.create(owner));sessions.revoke_account(owner['account_id'])
        self.assertTrue(all(sessions.authenticate(c) is None for c in cookies))
        self.assertIsNotNone(sessions.create(owner))


class AccountHTTPTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.DashboardAPITests();self.addCleanup(self.f.doCleanups);self.f.setUp()
        self.owner_password=secrets.token_urlsafe(24);self.viewer_password=secrets.token_urlsafe(24)

    def create(self,name,password,role):
        status,_,reply=self.f.http('POST','/api/accounts',dict(username=name,password=password,role=role))
        self.assertEqual(status,201,reply);return reply

    def login(self,name,password):
        status,headers,reply=self.f.http('POST','/api/login',dict(username=name,password=password),authenticated=False)
        self.assertEqual(status,200,reply)
        parsed=SimpleCookie(headers['Set-Cookie']);self.f.cookie=COOKIE+'='+parsed[COOKIE].value;self.f.csrf=reply['csrf']
        return headers

    def test_owner_password_restart_preserves_all_machine_identity_and_bytes(self):
        entry=self.f.upload()
        names=[self.f.controller/'controller/controller.json',self.f.controller/'controller/server.crt',
               *[n['root']/'node/node.json' for n in self.f.nodes],*[n['root']/'node/data/.asc-volume.json' for n in self.f.nodes]]
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
        methods=self.f.http('GET','/api/auth/methods',authenticated=False)[2];self.assertFalse(methods['password'])
        owner=self.create('primary',self.owner_password,'owner')
        self.assertTrue(self.f.http('GET','/api/auth/methods',authenticated=False)[2]['password'])
        headers=self.login('primary',self.owner_password)
        self.assertIn('Secure; HttpOnly; SameSite=Strict',headers['Set-Cookie'])
        self.assertEqual(self.f.http('GET','/api/session')[2]['role'],'owner')
        self.f.stop(self.f.controller_process);self.f.controller_process=self.f.start(self.f.controller,'run-controller')
        self.assertEqual(self.f.http('GET','/api/state')[0],401)
        self.login('primary',self.owner_password)
        self.assertEqual(self.f.http('GET','/api/accounts')[2]['accounts'][0]['account_id'],owner['account_id'])
        status,_,raw=self.f.http('GET','/api/files/'+entry['file']['file_id']+'/content',json_response=False)
        self.assertEqual((status,raw),(200,self.f.data))
        self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in names})

    def test_viewer_can_read_and_download_but_all_writes_and_account_access_denied(self):
        entry=self.f.upload();self.create('primary',self.owner_password,'owner');self.create('reader',self.viewer_password,'viewer')
        self.login('reader',self.viewer_password)
        caps=self.f.http('GET','/api/capabilities')[2]
        self.assertFalse(caps['node_management']);self.assertFalse(caps['file_upload']);self.assertFalse(caps['account_management'])
        self.assertFalse(caps['file_upload_download'])
        self.assertTrue(caps['file_download']);self.assertEqual(self.f.http('GET','/api/session')[2]['role'],'viewer')
        self.assertEqual(self.f.http('GET','/api/state')[0],200)
        status,_,raw=self.f.http('GET','/api/files/'+entry['file']['file_id']+'/content',json_response=False)
        self.assertEqual((status,raw),(200,self.f.data))
        for path in ('/api/uploads','/api/refresh','/api/v1/quick-join/pairings','/api/manage/v1/nodes/local-controller/preview',
                     '/api/manage/v1/confirm/anything','/api/accounts','/api/accounts/primary/change'):
            status,_,reply=self.f.http('POST',path,{})
            self.assertEqual((status,reply['error']),(403,'role_denied'),path)
        self.assertEqual(self.f.http('GET','/api/accounts')[0],403)
        self.assertEqual(self.f.http('GET','/api/manage/v1/nodes/'+self.f.nodes[0]['cfg']['node_id'])[0],403)
        self.assertEqual(self.f.http('POST','/api/logout',{})[0],200)

    def test_password_or_role_rotation_invalidates_old_cookie_and_fences_stale_update(self):
        self.create('primary',self.owner_password,'owner');reader=self.create('reader',self.viewer_password,'viewer')
        self.login('reader',self.viewer_password);old_cookie,old_csrf=self.f.cookie,self.f.csrf
        self.f.login()  # Local one-use owner recovery works even with password accounts enabled.
        password=secrets.token_urlsafe(24)
        update=dict(expected_generation=reader['generation'],role='owner',password=password,delete=False)
        self.assertEqual(self.f.http('POST','/api/accounts/reader/change',update)[0],200)
        self.assertEqual(self.f.http('GET','/api/state',headers={'Cookie':old_cookie,'X-ASC-CSRF':old_csrf})[0],401)
        self.assertEqual(self.f.http('POST','/api/accounts/reader/change',update)[0],409)
        self.assertEqual(self.f.http('POST','/api/login',dict(username='reader',password=self.viewer_password),authenticated=False)[0],401)
        self.login('reader',password)
        self.assertEqual(self.f.http('GET','/api/session')[2]['role'],'owner')
        self.assertTrue(self.f.http('GET','/api/capabilities')[2]['account_management'])

    def test_account_validation_csrf_last_owner_and_no_password_hash_response(self):
        self.assertEqual(self.f.http('POST','/api/accounts',dict(username='primary',password='short',role='owner'))[0],400)
        self.assertFalse((self.f.controller/'dashboard/accounts.json').exists())
        self.assertEqual(self.f.http('POST','/api/accounts',dict(username='primary',password=self.owner_password,role='owner'),
            headers={'Origin':'https://evil.invalid'})[0],403)
        owner=self.create('primary',self.owner_password,'owner');before=(self.f.controller/'dashboard/accounts.json').read_bytes()
        for role,delete in (('viewer',False),('owner',True)):
            status,_,reply=self.f.http('POST','/api/accounts/primary/change',dict(expected_generation=1,role=role,password='',delete=delete))
            self.assertEqual((status,reply['error']),(409,'last_owner_required'))
        status,_,listing=self.f.http('GET','/api/accounts')
        self.assertEqual(status,200);self.assertNotIn('password_hash',json.dumps(listing));self.assertNotIn('salt',json.dumps(listing))
        self.assertNotIn(self.owner_password,json.dumps(listing));self.assertEqual(listing['accounts'][0]['account_id'],owner['account_id'])
        self.assertEqual((self.f.controller/'dashboard/accounts.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
