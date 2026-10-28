"""Private owner CLI, actual installed Demo/TLS/bytes; no SSH or real phone."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
import uuid
from asc.access import maintenance
from asc.demo import upgrade
from asc.demo.package import digest, encoded
from tests import test_demo_upgrade as fixtures


class MaintenanceContractTests(unittest.TestCase):
    def plan(self):
        body=dict(format=1,kind='asc-private-maintenance',mode='single-writer-demo',action='upgrade',
            installation_id=str(uuid.uuid4()),role='node',current_release_id='a'*64,
            target_release_id='b'*64,backup_sha256='c'*64,state_formats=dict(maintenance.FORMATS))
        return dict(body,plan_sha256=digest(encoded(body)))
    def test_strict_contract_confirmation_and_no_command_fields(self):
        plan=self.plan();maintenance.validate(plan,plan['plan_sha256'])
        for changes in ({'format':True},{'mode':'core-quorum'},{'mode':'recovery-read-only'},
            {'action':'shell'},{'role':'voter'},{'installation_id':'new'},{'command':'anything'},
            {'target_release_id':'a'*64},{'state_formats':dict(maintenance.FORMATS,registry=99)}):
            bad=copy.deepcopy(plan);bad.update(changes)
            body={k:v for k,v in bad.items() if k!='plan_sha256'};bad['plan_sha256']=digest(encoded(body))
            with self.subTest(fields=list(changes)),self.assertRaises(ValueError):maintenance.validate(bad)
        with self.assertRaises(ValueError):maintenance.validate(plan,'d'*64)
        changed=dict(plan,backup_sha256='e'*64)
        with self.assertRaises(ValueError):maintenance.validate(changed)
    def test_unqualified_android_is_refused_before_legacy_context(self):
        with mock.patch.dict(os.environ,{'PREFIX':'/data/data/com.termux/files/usr'}):
            with self.assertRaises(ValueError):maintenance.platform_guard()


class MaintenanceInstalledTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.DemoUpgradeTests();self.addCleanup(self.f.doCleanups);self.f.setUp()
        self.repo=Path(__file__).resolve().parents[1]
    def cli(self,root,*args):
        return subprocess.run([sys.executable,'-m','asc.access.maintenance','--state',str(root),
            '--prefix',str(self.f.prefix_for(root)),*map(str,args)],cwd=self.repo,env=self.f.env,
            capture_output=True,text=True,timeout=45)
    def prepare(self,root,target,label):
        backup=self.f.home/(label+'-preflight-backup');self.f.command(root,'backup',str(backup))
        result=self.cli(root,'preflight','--target',target,'--backup',backup)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr);plan=json.loads(result.stdout)
        path=self.f.home/(label+'-plan.json');path.write_text(json.dumps(plan));path.chmod(0o600)
        return backup,plan,path
    def apply(self,root,backup,plan,path,new_backup):
        return self.cli(root,'apply','--plan',path,'--backup',backup,'--new-backup',new_backup,
            '--confirm-plan',plan['plan_sha256'])

    def test_actual_controller_and_node_upgrade_retry_new_writes_and_code_only_rollback(self):
        first=self.f.upload();self.f.stop_all();source,target=self.f.candidate()
        records=[]
        for index,root in enumerate((self.f.controller,self.f.bphone)):
            prefix=self.f.prefix_for(root);old=json.loads((prefix/'install.json').read_text())['release_id']
            identity=self.f.identity_bytes(root);self.f.command(root,'stage',str(source))
            backup,plan,path=self.prepare(root,target,'node'+str(index))
            new=self.f.home/('node'+str(index)+'-activation-backup')
            result=self.apply(root,backup,plan,path,new);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertFalse(json.loads(result.stdout)['already_applied'])
            retry=self.apply(root,backup,plan,path,new);self.assertEqual(retry.returncode,0,retry.stdout+retry.stderr)
            self.assertTrue(json.loads(retry.stdout)['already_applied']);self.assertEqual(self.f.identity_bytes(root),identity)
            records.append((root,old,identity))
        self.f.controller_process=self.f.start(self.f.controller,'run-controller')
        from asc.client import request_json
        self.f.wait_for(lambda:request_json(self.f.origin,self.f.pin,'GET','/api/v1/info'))
        for node in self.f.nodes:node['process']=self.f.start(node['root'],'run-node')
        self.f.wait_for(lambda:self.f.command(self.f.controller,'replicas',first['file']['file_id'])['available_replicas']==2)
        second=self.f.upload(key='maintenance_new_version',path='maintenance/new-after-upgrade.bin')
        self.f.stop_all()
        for index,(root,old,identity) in enumerate(records):
            backup=self.f.home/('rollback'+str(index)+'-NEW-state-backup');self.f.command(root,'backup',str(backup))
            result=self.cli(root,'preflight','--target',old,'--backup',backup,'--action','rollback')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);plan=json.loads(result.stdout)
            path=self.f.home/('rollback'+str(index)+'-plan.json');path.write_text(json.dumps(plan));path.chmod(0o600)
            result=self.apply(root,backup,plan,path,self.f.home/('rollback'+str(index)+'-activation-backup'))
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertFalse(json.loads(result.stdout)['state_restored'])
            self.assertEqual(self.f.identity_bytes(root),identity)
        self.f.controller_process=self.f.start(self.f.controller,'run-controller')
        self.f.wait_for(lambda:request_json(self.f.origin,self.f.pin,'GET','/api/v1/info'))
        for node in self.f.nodes:node['process']=self.f.start(node['root'],'run-node')
        self.f.wait_for(lambda:self.f.command(self.f.controller,'replicas',second['file']['file_id'])['available_replicas']==2)
        for index,file in enumerate((first,second)):
            output=self.f.home/('post-rollback-'+str(index)+'.bin')
            self.f.command(self.f.controller,'download',file['file']['file_id'],str(output));self.assertEqual(output.read_bytes(),self.f.data)

    def test_running_changed_state_corrupt_backup_and_wrong_confirmation_refuse(self):
        self.f.upload();source,target=self.f.candidate();root=self.f.controller;self.f.command(root,'stage',str(source))
        absent=self.f.home/'no-backup-created'
        self.assertNotEqual(self.cli(root,'preflight','--target',target,'--backup',absent).returncode,0)
        self.assertFalse(absent.exists());self.f.stop_all()
        backup,plan,path=self.prepare(root,target,'refusal');pointer=(self.f.prefix_for(root)/'install.json').read_bytes()
        blocked=self.f.home/'blocked-activation'
        result=self.cli(root,'apply','--plan',path,'--backup',backup,'--new-backup',blocked,'--confirm-plan','0'*64)
        self.assertNotEqual(result.returncode,0)
        changed=root/'test-owned-state-change';changed.write_bytes(b'new state after preflight')
        self.assertNotEqual(self.apply(root,backup,plan,path,blocked).returncode,0);changed.unlink()
        probe=next((backup/'state/node/data/objects').glob('*.blob'));probe.write_bytes(b'test-owned corruption')
        self.assertNotEqual(self.apply(root,backup,plan,path,blocked).returncode,0)
        self.assertEqual((self.f.prefix_for(root)/'install.json').read_bytes(),pointer);self.assertFalse(blocked.exists())
        self.assertNotIn(self.f.admin(),result.stdout+result.stderr)

    def test_final_lock_recheck_refuses_stale_release_or_backup_after_plan_validation(self):
        self.f.upload();self.f.stop_all();source,target=self.f.candidate();root=self.f.controller
        self.f.command(root,'stage',str(source));backup,plan,path=self.prepare(root,target,'cas')
        prefix=self.f.prefix_for(root);before=(prefix/'install.json').read_bytes()
        # Exercise the SAME final critical section the adapter invokes. No mocked
        # successful activation; current release/backup must be proven under locks.
        with mock.patch.dict(os.environ,self.f.env):
            for expected in ((plan['installation_id'],'e'*64), (str(uuid.uuid4()),plan['current_release_id'])):
                with self.assertRaises(ValueError):upgrade.activate(root,prefix,target,self.f.home/'cas-blocked',
                    expected_current=expected,verified_backup=(backup,plan['backup_sha256']))
            with self.assertRaises(ValueError):upgrade.activate(root,prefix,target,self.f.home/'cas-blocked',
                expected_current=(plan['installation_id'],plan['current_release_id']),verified_backup=(backup,'e'*64))
            changed=root/'test-owned-final-cas';changed.write_bytes(b'changed in preflight/activate gap')
            with self.assertRaises(ValueError):upgrade.activate(root,prefix,target,self.f.home/'cas-blocked',
                expected_current=(plan['installation_id'],plan['current_release_id']),verified_backup=(backup,plan['backup_sha256']))
        self.assertEqual((prefix/'install.json').read_bytes(),before);self.assertFalse((self.f.home/'cas-blocked').exists())

    def test_interrupted_guarded_activation_requires_existing_recovery_not_retry_or_reinit(self):
        self.f.upload();self.f.stop_all();source,target=self.f.candidate();root=self.f.controller
        self.f.command(root,'stage',str(source));backup,plan,path=self.prepare(root,target,'interruption')
        prefix=self.f.prefix_for(root);identity=self.f.identity_bytes(root);new=self.f.home/'interrupted-maintenance'
        original=upgrade.durable_json
        def interrupted(path,value):
            if path.name=='upgrade-journal.json' and value.get('status')=='COMPLETED':raise OSError('synthetic interrupted completion')
            return original(path,value)
        with mock.patch.dict(os.environ,self.f.env),mock.patch.object(upgrade,'durable_json',side_effect=interrupted):
            with self.assertRaises(OSError):maintenance.apply(root,prefix,plan,backup,new,plan['plan_sha256'])
        self.assertEqual(json.loads((prefix/'upgrade-journal.json').read_text())['status'],'PREPARED')
        self.assertEqual(self.f.identity_bytes(root),identity)
        self.assertNotEqual(self.apply(root,backup,plan,path,new).returncode,0)
        recovered=self.f.command(root,'recover-upgrade');self.assertFalse(recovered['state_restored'])
        self.assertEqual(recovered['release_id'],plan['current_release_id']);self.assertEqual(self.f.identity_bytes(root),identity)

    def test_no_recovery_core_protected_unknown_or_symlink_adoption(self):
        self.f.stop_all();source,target=self.f.candidate();root=self.f.controller;self.f.command(root,'stage',str(source))
        backup,plan,path=self.prepare(root,target,'guards');pointer=(self.f.prefix_for(root)/'install.json').read_bytes()
        for model in ('SM-M515F','unknown',''):
            old=self.f.env['ASC_TEST_MODEL'];self.f.env['ASC_TEST_MODEL']=model
            result=self.apply(root,backup,plan,path,self.f.home/'guard-blocked');self.f.env['ASC_TEST_MODEL']=old
            self.assertNotEqual(result.returncode,0)
        for marker in (root/'RECOVERY_READ_ONLY.json',root/'controller/consensus.json'):
            marker.write_text('{}');self.assertNotEqual(self.apply(root,backup,plan,path,self.f.home/'guard-blocked').returncode,0);marker.unlink()
        link=self.f.home/'plan-link.json';link.symlink_to(path)
        self.assertNotEqual(self.apply(root,backup,plan,link,self.f.home/'guard-blocked').returncode,0)
        self.assertEqual((self.f.prefix_for(root)/'install.json').read_bytes(),pointer);self.assertFalse((self.f.home/'guard-blocked').exists())
