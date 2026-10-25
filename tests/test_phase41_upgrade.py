"""Exact published Phase4.0 archive ->current candidate; no stale DB rollback."""
import contextlib
import hashlib
import json
import sqlite3
import subprocess
import tarfile
from asc.client import request_json
from asc.demo.package import verify
from tests import test_demo_lan as lan
from tests import test_demo_upgrade as installed
from tests import test_demo_release_upgrade as historical
from tests import test_quick_join as quick


class Phase41UpgradeTests(historical.PublishedUpgradeFixture):
    proxy=quick.QuickJoinTests.proxy
    quick_join=quick.QuickJoinTests.join

    def command_result(self,root,*args,input=None):
        if not hasattr(self,'candidate_source'):
            self.candidate_source=self.source
            self.candidate_release=verify(self.source)
            self.assertEqual(self.candidate_release['version'],'0.4.3-dev')
            published=self.repo/'candidates/asc-demo-alpha-0.4.3-dev.tar.gz'
            self.assertEqual(self.archive.read_bytes(),published.read_bytes(), 'Exact candidate must match source build')
            archive=self.repo/'candidates/asc-demo-alpha-0.4.2-dev.tar.gz'
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),
                'b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3')
            with tarfile.open(archive) as saved:
                self.assertTrue(all(m.isfile() and not m.name.startswith('/') and '..' not in m.name.split('/') for m in saved.getmembers()))
                saved.extractall(self.root/'exact-phase40',filter='data')
            self.old_source=self.root/'exact-phase40/asc-demo-alpha'
            self.old_release=verify(self.old_source);self.source=self.old_source
            self.assertEqual(self.old_release['version'],'0.4.2-dev')
            self.assertEqual(self.old_release['state_formats'],self.candidate_release['state_formats'])
        return installed.DemoUpgradeTests.command_result(self,root,*args,input=input)

    def test_exact042_to043_pending_bridge_identity_new_state_code_rollback_and_reverse_pending(self):
        old_file=self.upload()
        pending_root=self.home/'old-pending-node'
        self.command(pending_root,'init','--role','node','--host','127.0.0.1')
        code=self.command(self.controller,'pair')['code']
        proxy,proxy_origin=self.proxy(drop=True)
        old_join=self.command_result(pending_root,'join','--controller',proxy_origin,'--pin',self.pin,
            '--name','pending old042',input=code+'\n')
        self.assertNotEqual(old_join.returncode,0);self.assertTrue(proxy.dropped)
        old_pending=(pending_root/'node/enrollment_pending.json').read_bytes()
        self.assertFalse((pending_root/'node/node.json').exists())
        pending=json.loads(old_pending)
        self.stop_all()
        port=self.free_port();self.command(self.controller,'dashboard-init','--port',str(port))
        browser_files={p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()}
        roots=[self.controller,self.bphone,pending_root]
        identities={str(r):self.identity_bytes(r) for r in roots}
        candidate=self.candidate_release['release_id'];old_id=self.old_release['release_id']
        for root in roots:
            backup=self.home/(root.name+'-042-before')
            self.command(root,'backup',str(backup));self.command(root,'verify-backup',str(backup))
            self.assertEqual(self.command(root,'stage',str(self.candidate_source))['release_id'],candidate)
            self.assertTrue(self.command(root,'upgrade-preflight',candidate)['compatible'])
            activated=self.command(root,'upgrade',candidate,'--backup',str(self.home/(root.name+'-activation')))
            self.assertFalse(activated['schema_migration']);self.assertEqual(activated['previous_release_id'],old_id)
            self.assertEqual(self.identity_bytes(root),identities[str(root)])
            self.command(root,'verify-backup',str(self.home/(root.name+'-activation')))
        self.assertEqual((pending_root/'node/enrollment_pending.json').read_bytes(),old_pending)
        self.assertEqual({p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()},browser_files)
        self.source=self.candidate_source;self.browser_enabled=True;self.restart_cluster()
        # Real installed bridge against upgraded enrolled Engine; separate private
        # app authorization/journal survive code rollback, not part of engine DB.
        control=self.home/'phase41-private-control'
        self.command(self.bphone,'bridge-provision','--control',str(control))
        process=subprocess.Popen(['sh',str(self.prefix_for(self.bphone)/'bin/asc-demo'),'--state',str(self.bphone),
            'bridge-run','--control',str(control)],cwd=self.root,env=self.env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop,process)
        self.wait_for(lambda:(control/'engine.sock').exists())
        status=self.command(self.bphone,'bridge-status','--control',str(control))
        self.assertTrue(status['ok']);self.assertTrue(status['result']['node']['identity_present'])
        self.assertIsNone(status['result']['volumes'][0]['writable'])
        self.stop(process)
        control_bytes={p.name:p.read_bytes() for p in control.iterdir() if p.is_file()}
        self.wait_for(lambda:self.command(self.controller,'replicas',old_file['file']['file_id'])['available_replicas']==2)
        output=self.home/'candidate-old-download';self.command(self.controller,'download',old_file['file']['file_id'],str(output))
        self.assertEqual(hashlib.sha256(output.read_bytes()).digest(),hashlib.sha256(self.data).digest())
        pair={'controller':proxy_origin,'pin':self.pin,'cluster_id':pending['expected_cluster_id'],'code':code}
        resumed=self.quick_join(pending_root,pair)
        self.assertEqual(resumed.returncode,0,'Phase4.0 pending did not resume; private output suppressed')
        node=json.loads((pending_root/'node/node.json').read_bytes())
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
            operation=db.execute('SELECT node_id FROM enrollments WHERE enrollment_hash=?',(hashlib.sha256(pending['payload']['enrollment_id'].encode()).hexdigest(),)).fetchone()
            self.assertEqual(operation[0],node['node_id'])
            self.assertEqual(node['token'],pending['payload']['enrollment_token'])
        self.assertEqual(proxy.join_calls,2)
        self.assertFalse((pending_root/'node/storage.json').exists())
        identities[str(pending_root)]=self.identity_bytes(pending_root)
        new_file=self.upload('phase4_new_file_key','demo/new-under-phase4.bin')
        self.assertEqual(new_file['verified_replicas'],2)
        # Create pending in NEW code, then resume with EXACT OLD code after rollback.
        reverse_root=self.home/'candidate-pending-node'
        self.command(reverse_root,'init','--role','node','--host','127.0.0.1')
        reverse_code=self.command(self.controller,'pair')['code'];proxy.drop=True;proxy.dropped=False
        pair=dict(pair,code=reverse_code)
        failed=self.quick_join(reverse_root,pair)
        self.assertNotEqual(failed.returncode,0);self.assertTrue(proxy.dropped)
        reverse_pending=(reverse_root/'node/enrollment_pending.json').read_bytes()
        reverse=json.loads(reverse_pending)
        identities[str(reverse_root)]=self.identity_bytes(reverse_root);roots.append(reverse_root)
        self.stop_all()
        for root in roots:
            # Fresh code-only rollback uses a NEW full backup of NEW state.
            self.command(root,'stage',str(self.old_source))
            backup=self.home/(root.name+'-new-state-before-rollback')
            rolled=self.command(root,'rollback',old_id,'--backup',str(backup))
            self.assertFalse(rolled['schema_migration']);self.command(root,'verify-backup',str(backup))
            self.assertEqual(self.identity_bytes(root),identities[str(root)])
            self.assertEqual(json.loads((self.prefix_for(root)/'install.json').read_bytes())['release_id'],old_id)
        self.assertEqual((reverse_root/'node/enrollment_pending.json').read_bytes(),reverse_pending)
        self.source=self.old_source;self.restart_cluster()
        legacy=self.command_result(reverse_root,'join','--controller',proxy_origin,'--pin',self.pin,
            '--name',reverse['payload']['name'],input='')
        self.assertEqual(legacy.returncode,0,'Old code could not resume candidate pending; private output suppressed')
        cfg=json.loads((reverse_root/'node/node.json').read_bytes())
        self.assertEqual(cfg['token'],reverse['payload']['enrollment_token'])
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT node_id FROM enrollments WHERE enrollment_hash=?',(hashlib.sha256(reverse['payload']['enrollment_id'].encode()).hexdigest(),)).fetchone()[0],cfg['node_id'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_files').fetchone()[0],2)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],4)
            for root in (pending_root,reverse_root):
                joined=json.loads((root/'node/node.json').read_bytes())
                self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes WHERE node_id=?',(joined['node_id'],)).fetchone()[0],0)
        for saved in (old_file,new_file):
            fid=saved['file']['file_id']
            self.wait_for(lambda:self.command(self.controller,'replicas',fid)['available_replicas']==2)
            target=self.home/('old-code-download-'+fid)
            self.command(self.controller,'download',fid,str(target))
            self.assertEqual(hashlib.sha256(target.read_bytes()).digest(),hashlib.sha256(self.data).digest())
        self.assertEqual({p.name:p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()},browser_files)
        for root in roots[:-1]:self.assertEqual(self.identity_bytes(root),identities[str(root)])
        self.assertEqual({p.name:p.read_bytes() for p in control.iterdir() if p.is_file()},control_bytes)
        self.assertNotEqual(self.command_result(self.bphone,'bridge-status','--control',str(control)).returncode,0,
            'Old source must refuse unsupported bridge API; never silently fall back')
