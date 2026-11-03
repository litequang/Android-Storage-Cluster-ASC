"""Actual owner preferences/diagnostics, no machine-identity or data mutation."""
from contextlib import closing
import hashlib
import json
import secrets
import sqlite3
import unittest
from tests import test_demo_dashboard as fixture


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.DashboardAPITests();self.addCleanup(self.f.doCleanups);self.f.setUp()

    def test_preferences_cas_restart_preserves_credentials_and_real_file_bytes(self):
        file=self.f.send_file();roots=[self.f.controller/'controller/controller.json',*[n['root']/'node/node.json' for n in self.f.nodes]]
        identities=[p.read_bytes() for p in roots]
        status,_,old=self.f.http('GET','/api/preferences');self.assertEqual(status,200)
        self.assertEqual(old['revision'],0);self.assertFalse((self.f.controller/'dashboard/preferences.json').exists())
        obj=dict(preferences_api_version=1,expected_revision=old['revision'],display_name='<img src=x onerror=alert(1)> owner',refresh_seconds=5)
        status,_,new=self.f.http('POST','/api/preferences',obj);self.assertEqual(status,200,new)
        self.assertEqual(new['revision'],1);self.assertEqual(self.f.http('POST','/api/preferences',obj)[0],409)
        self.assertEqual((self.f.controller/'dashboard/preferences.json').stat().st_mode&0o777,0o600)
        self.f.stop(self.f.controller_process);self.f.controller_process=self.f.start(self.f.controller,'run-controller');self.f.login()
        self.assertEqual(self.f.http('GET','/api/preferences')[2]['display_name'],obj['display_name'])
        self.assertTrue([p.read_bytes() for p in roots]==identities,'identity changed; private values suppressed')
        status,headers,raw=self.f.http('GET','/api/files/'+file['file_id']+'/content',json_response=False)
        self.assertEqual((status,raw),(200,self.f.data));self.assertEqual(headers['X-ASC-SHA256'],hashlib.sha256(raw).hexdigest())

    def test_diagnostic_export_redacts_names_ids_paths_credentials_and_creates_no_state(self):
        self.f.upload(path='private-folder/secret-file.bin')
        before={p.name for p in (self.f.controller/'dashboard').iterdir()}
        status,_,report=self.f.http('GET','/api/diagnostics');self.assertEqual(status,200,report)
        serialized=json.dumps(report)
        cluster=json.loads((self.f.controller/'controller/controller.json').read_bytes())['cluster_id']
        for forbidden in (self.f.admin(),self.f.nodes[0]['cfg']['token'],cluster,self.f.nodes[0]['cfg']['node_id'],
                          self.f.pin,self.f.nodes[0]['pin'],self.f.origin,str(self.f.controller),'private-folder','secret-file.bin','synthetic-phone-0'):
            self.assertNotIn(forbidden,serialized)
        self.assertEqual(report['diagnostic_api_version'],1);self.assertEqual(report['counts']['files'],1)
        self.assertTrue(all(v['fsync_tested'] is True for n in report['nodes'] for v in n['volumes']))
        self.assertTrue(all(not value for value in report['features'].values()))
        self.assertEqual(before,{p.name for p in (self.f.controller/'dashboard').iterdir()})

    def test_strict_inputs_owner_viewer_and_unsafe_state_refuse_without_reset(self):
        base=dict(preferences_api_version=1,expected_revision=0,display_name='Owner label',refresh_seconds=10)
        for changes in ({'refresh_seconds':True},{'refresh_seconds':4},{'refresh_seconds':61},{'display_name':''},
                        {'display_name':'bad\nname'},{'expected_revision':True},{'format':2},{'admin_token':'forbidden'}):
            self.assertEqual(self.f.http('POST','/api/preferences',base|changes)[0],400,changes)
        self.assertEqual(self.f.http('POST','/api/preferences',base,authenticated=False)[0],401)
        self.assertEqual(self.f.http('POST','/api/preferences',base,headers={'Origin':'https://evil.invalid'})[0],403)
        self.assertEqual(self.f.http('POST','/api/preferences',base)[0],200)
        path=self.f.controller/'dashboard/preferences.json';original=path.read_bytes();path.write_bytes(b'{}')
        self.assertEqual(self.f.http('GET','/api/preferences')[0],503);self.assertEqual(path.read_bytes(),b'{}');path.write_bytes(original)
        path.chmod(0o644);self.assertEqual(self.f.http('GET','/api/preferences')[0],503);path.chmod(0o600)
        held=path.with_suffix('.held');path.rename(held);path.symlink_to(held)
        self.assertEqual(self.f.http('GET','/api/preferences')[0],503);path.unlink();held.rename(path)
        password=secrets.token_urlsafe(24)
        for name,role in (('primary','owner'),('reader','viewer')):
            self.assertEqual(self.f.http('POST','/api/accounts',dict(username=name,role=role,password=password))[0],201)
        status,headers,reply=self.f.http('POST','/api/login',dict(username='reader',password=password),authenticated=False)
        self.assertEqual(status,200);self.f.cookie=headers['Set-Cookie'].split(';')[0];self.f.csrf=reply['csrf']
        self.assertEqual(self.f.http('GET','/api/preferences')[0],200)
        self.assertEqual(self.f.http('POST','/api/preferences',base)[0],403);self.assertEqual(self.f.http('GET','/api/diagnostics')[0],403)

    def test_stale_probe_preserves_unknown_fsync_capacity_and_does_not_become_zero(self):
        self.f.stop(self.f.controller_process)
        from asc.store import Registry
        from asc.demo.dashboard.views import Views
        from asc.catalog.state import Catalog
        from types import SimpleNamespace
        registry=Registry(self.f.controller/'controller/registry.sqlite3')
        with registry.connect() as db:db.execute('UPDATE catalog_nodes SET checked_at=0')
        state=Views(SimpleNamespace(registry=registry,catalog=Catalog(registry)),'known cluster').state()
        self.assertIsNone(state['capacity']['available_bytes'])
        for node in state['nodes']:
            for v in node['volumes']:
                self.assertIsNone(v['fsync_tested']);self.assertIsNone(v['free_bytes']);self.assertIsNone(v['writable'])


if __name__=='__main__':unittest.main()
