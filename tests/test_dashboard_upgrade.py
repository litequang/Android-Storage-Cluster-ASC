"""Exact shipped b423/043 -> current source -> NEW-state code rollback, real I/O."""
import hashlib
import json
import secrets
import ssl
import tarfile
import uuid
from asc.demo import package
from asc.client import request_json
from tests import test_demo_release_upgrade as published
from tests import test_demo_upgrade as installed
from tests import test_demo_dashboard as browser


class DashboardUpgradeTests(published.PublishedUpgradeFixture):
    http=browser.DashboardAPITests.http
    login=browser.DashboardAPITests.login

    def command_result(self,root,*args,input=None):
        if not hasattr(self,'old_source'):
            archive=self.repo/'candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz'
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),'6a60bd4180bc338d8c62eff4ef1347082a0e6c0ce36e06143ff53baa791b9d57')
            with tarfile.open(archive) as saved:saved.extractall(self.root/'exact043',filter='data')
            self.old_source=self.root/'exact043/asc-demo-alpha';self.old_release=package.verify(self.old_source)
            self.assertEqual(self.old_release['release_id'],'b423c5d8e811876ae71a9e0ad41c6ba46acc5b4056b408a8e125875aabcf2aca')
            current=self.root/'current-dashboard-source.tar.gz';package.build(self.repo,current)
            with tarfile.open(current) as saved:saved.extractall(self.root/'current',filter='data')
            self.new_source=self.root/'current/asc-demo-alpha';self.new_release=package.verify(self.new_source)
            for name in ('asc/demo/dashboard/history.py','asc/catalog/audit.py','asc/demo/dashboard/accounts.py'):
                self.assertEqual((self.new_source/name).read_bytes(),(self.repo/name).read_bytes())
            self.assertEqual(self.new_release['state_formats'],self.old_release['state_formats'])
            self.source=self.old_source
        return installed.DemoUpgradeTests.command_result(self,root,*args,input=input)

    def web_ready(self):
        self.browser_origin='https://127.0.0.1:'+str(self.dashboard_port)
        self.context=ssl.create_default_context(cafile=str(self.controller/'dashboard/ca.crt'))
        self.cookie,self.csrf='',''
        self.wait_for(lambda:self.http('GET','/api/auth/methods',authenticated=False)[0]==200)
        self.login()

    def test_exact043_upgrade_accounts_snapshot_restore_new_state_rollback_and_forward(self):
        old=self.upload();old_id=old['file']['file_id'];roots=[self.controller,self.bphone]
        identities={str(root):self.identity_bytes(root) for root in roots}
        self.stop_all();self.dashboard_port=self.free_port()
        self.command(self.controller,'dashboard-init','--port',str(self.dashboard_port))
        tls={p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()}
        for root in roots:
            backup=self.home/(root.name+'-before-dashboard')
            self.command(root,'backup',str(backup));self.command(root,'verify-backup',str(backup))
            self.command(root,'stage',str(self.new_source))
            self.assertTrue(self.command(root,'upgrade-preflight',self.new_release['release_id'])['compatible'])
            result=self.command(root,'upgrade',self.new_release['release_id'],'--backup',str(self.home/(root.name+'-dashboard-activation')))
            self.assertFalse(result['schema_migration'])
            self.assertTrue(self.identity_bytes(root)==identities[str(root)],'identity changed; private values suppressed')
        self.source=self.new_source;self.browser_enabled=True;self.restart_cluster();self.web_ready()
        self.wait_for(lambda:self.command(self.controller,'replicas',old_id)['available_replicas']==2)
        password=secrets.token_urlsafe(24)
        self.assertEqual(self.http('POST','/api/accounts',dict(username='primary',password=password,role='owner'))[0],201)
        snapshot=dict(history_api_version=1,request_id=str(uuid.uuid4()),label='Upgrade proof',prefix='')
        status,_,reply=self.http('POST','/api/history/snapshots',snapshot);self.assertEqual(status,201)
        sid=reply['snapshot_id'];self.wait_for(lambda:self.http('POST','/api/history/snapshots/'+sid+'/step',{})[2]['state']=='VERIFIED')
        restore=dict(history_api_version=1,request_id=str(uuid.uuid4()),file_id=old_id,snapshot_id=sid)
        status,_,reply=self.http('POST','/api/history/restores',restore);self.assertEqual(status,201)
        rid=reply['restore_id'];self.wait_for(lambda:self.http('POST','/api/history/restores/'+rid+'/step',{})[2]['state']=='COMPLETED')
        state=self.http('GET','/api/history')[2];target=state['restores'][rid]['target_file_id']
        optional={p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()}
        self.assertEqual({name:optional[name] for name in tls},tls)
        self.stop_all()
        for root in roots:
            self.command(root,'stage',str(self.old_source));backup=self.home/(root.name+'-NEW-state-rollback')
            result=self.command(root,'rollback',self.old_release['release_id'],'--backup',str(backup))
            self.assertFalse(result['schema_migration']);self.command(root,'verify-backup',str(backup))
            self.assertTrue(self.identity_bytes(root)==identities[str(root)],'identity changed; private values suppressed')
        self.assertTrue({p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()}==optional)
        self.source=self.old_source;self.restart_cluster()
        self.wait_for(lambda:request_json(self.origin,self.pin,'GET','/api/v1/info'))
        self.wait_for(lambda:self.command(self.controller,'replicas',target)['available_replicas']==2)
        for fid in (old_id,target):
            out=self.home/('rollback-'+fid+'.bin');self.command(self.controller,'download',fid,str(out))
            self.assertTrue(out.read_bytes()==self.data,'old code lost current immutable bytes')
        # Old code ignores optional account/history files; no stale DB restoration.
        self.stop_all()
        for root in roots:
            self.command(root,'upgrade',self.new_release['release_id'],'--backup',str(self.home/(root.name+'-forward-backup')))
        self.source=self.new_source;self.restart_cluster();self.web_ready()
        self.assertEqual(self.http('GET','/api/history')[2]['snapshots'][sid]['manifest_sha256'],state['snapshots'][sid]['manifest_sha256'])
        self.assertEqual(self.http('GET','/api/history')[2]['restores'][rid]['state'],'COMPLETED')
        self.assertEqual(self.http('POST','/api/login',dict(username='primary',password=password),authenticated=False)[0],200)
        self.assertTrue({p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()}==optional)
