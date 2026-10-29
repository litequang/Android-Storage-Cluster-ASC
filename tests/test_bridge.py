"""Actual private UDS / existing TLS engine enrollment, no real phone or mock success."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import time
import unittest
from unittest import mock
from asc.bridge.service import provision, Runtime, call, Bridge
from asc.bridge.contract import Refused
from tests import test_quick_join as fixture


class BridgeTests(unittest.TestCase):
    script=fixture.QuickJoinTests.script
    run_cli=fixture.QuickJoinTests.run_cli
    free_port=staticmethod(fixture.QuickJoinTests.free_port)
    command_result=fixture.QuickJoinTests.command_result
    command=fixture.QuickJoinTests.command
    stop=fixture.QuickJoinTests.stop
    wait_for=fixture.QuickJoinTests.wait_for
    seen=fixture.QuickJoinTests.seen
    admin=fixture.QuickJoinTests.admin
    upload=fixture.QuickJoinTests.upload
    start=fixture.QuickJoinTests.start
    login=fixture.QuickJoinTests.login
    http=fixture.QuickJoinTests.http
    setUp=fixture.QuickJoinTests.setUp
    fresh=fixture.QuickJoinTests.fresh
    pairing=fixture.QuickJoinTests.pairing
    proxy=fixture.QuickJoinTests.proxy

    def control(self,root,scopes=('read','join')):
        path=self.home/(root.name+'-bridge')
        with mock.patch.dict(os.environ,self.env):provision(path,root,scopes)
        return path

    def params(self,pair):
        return dict(controller=pair['controller'],pin=pair['pin'],cluster_id=pair['cluster_id'],name='Bridge synthetic',code=pair['code'])

    def test_actual_socket_scope_peer_auth_framing_and_read_only_status(self):
        control=self.control(self.controller,('read',))
        with mock.patch.dict(os.environ,self.env), Runtime(control) as runtime:
            self.assertEqual((control/'engine.sock').stat().st_mode & 0o777,0o600)
            status=call(control,'status');self.assertTrue(status['ok'])
            report=status['result'];self.assertTrue(report['node']['identity_present']);self.assertEqual(len(report['volumes']),1)
            self.assertTrue(report['volumes'][0]['readable']);self.assertIsNone(report['volumes'][0]['writable'])
            self.assertIsNone(report['volumes'][0]['fsync_tested']);self.assertFalse(report['write_probe_performed'])
            self.assertEqual(report['controller']['state'],'ONLINE');self.assertFalse(report['controller']['writer_authority'])
            pair=self.pairing();self.assertEqual(call(control,'quick_join',self.params(pair))['error'],'scope_denied')
            auth=json.loads((control/'client.json').read_bytes())
            value=dict(api_version=1,request_id='11111111-1111-4111-8111-111111111111',app_id=auth['app_id'],authorization=auth['authorization'],operation='status',params={})
            with self.assertRaises(Refused):runtime.bridge.dispatch(value,os.getuid()+1)
            value['authorization']=self.nodes[0]['cfg']['token']
            with self.assertRaises(Refused):runtime.bridge.dispatch(value,os.getuid())
            for raw in (b'{"x":1,"x":2}\n',b'[]\n',b'x'*9000+b'\n'):
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                    connection.connect(str(control/'engine.sock'));connection.sendall(raw)
                    reply=json.loads(connection.makefile('rb').readline())
                    self.assertFalse(reply['ok']);self.assertEqual(reply['error'],'invalid_frame')
            serialized=json.dumps(report)
            for secret in (auth['authorization'],self.admin(),self.nodes[0]['cfg']['token']):self.assertNotIn(secret,serialized)
        self.assertFalse((control/'engine.sock').exists())

    def test_real_quick_join_same_request_retry_receipt_and_no_automatic_approval(self):
        root=self.fresh();control=self.control(root);pair=self.pairing();params=self.params(pair)
        request_id='11111111-1111-4111-8111-111111111111'
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            joined=call(control,'quick_join',params,request_id);self.assertTrue(joined['ok'],joined)
            result=joined['result'];self.assertEqual(result['approval_state'],'PENDING_OWNER_APPROVAL')
            cfg=(root/'node/node.json').read_bytes();self.assertFalse((root/'node/storage.json').exists())
            replay=call(control,'quick_join',params,request_id)
            self.assertTrue(replay['replayed']);self.assertTrue(replay['historical_receipt']);self.assertEqual(replay['result'],result)
            self.assertEqual((root/'node/node.json').read_bytes(),cfg)
            changed=dict(params,name='different intent')
            self.assertEqual(call(control,'quick_join',changed,request_id)['error'],'request_id_conflict')
            self.assertEqual(call(control,'quick_join',dict(params,code='000000000000'),request_id)['error'],'request_id_conflict')
            with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes WHERE node_id=?',(result['node_id'],)).fetchone()[0],0)
            for f in ('bridge.json','requests.sqlite3'):
                self.assertNotIn(pair['code'].encode(),(control/f).read_bytes())
                self.assertNotIn(json.loads(cfg)['token'].encode(),(control/f).read_bytes())
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            self.assertTrue(call(control,'quick_join',params,request_id)['replayed'])

    def test_successful_tls_ack_loss_then_bridge_restart_resumes_same_engine_operation(self):
        root=self.fresh();control=self.control(root);pair=self.pairing();proxy,origin=self.proxy(drop=True)
        params=dict(self.params(pair),controller=origin);rid='11111111-1111-4111-8111-111111111111'
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            reply=call(control,'quick_join',params,rid);self.assertFalse(reply['ok']);self.assertTrue(proxy.dropped)
            pending=json.loads((root/'node/enrollment_pending.json').read_bytes())
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            resumed={k:v for k,v in params.items() if k!='code'}
            reply=call(control,'quick_join',resumed,rid);self.assertTrue(reply['ok'],reply)
            cfg=json.loads((root/'node/node.json').read_bytes());self.assertEqual(cfg['token'],pending['payload']['enrollment_token'])
            self.assertFalse((root/'node/enrollment_pending.json').exists());self.assertEqual(proxy.join_calls,2)

    def test_wrong_pin_cluster_missing_state_recovery_and_replacement_denied(self):
        root=self.fresh();control=self.control(root);pair=self.pairing()
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            self.assertEqual(call(control,'quick_join',dict(self.params(pair),pin='0'*64))['error'],'tls_pin_mismatch')
            self.assertEqual(call(control,'quick_join',dict(self.params(pair),cluster_id='11111111-1111-4111-8111-111111111111'))['error'],'cluster_mismatch')
            self.assertFalse((root/'node/enrollment_pending.json').exists())
            (root/'RECOVERY_READ_ONLY.json').write_text('{}')
            self.assertFalse(call(control,'status')['ok'])
        before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        with mock.patch.dict(os.environ,self.env), self.assertRaises(ValueError):provision(self.home/'no-recovery-control',root)
        self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
        with mock.patch.dict(os.environ,self.env), self.assertRaises(ValueError):provision(self.home/'no-missing-control',self.home/'missing-state')
        self.assertFalse((self.home/'missing-state').exists())

    def test_private_control_paths_foreign_socket_and_journal_bounds_fail_closed(self):
        root=self.fresh();control=self.control(root)
        with mock.patch.dict(os.environ,self.env), self.assertRaises(FileExistsError):provision(control,root)
        outside=self.home/'outside-owned-sentinel';outside.write_bytes(b'unchanged')
        (control/'engine.sock').symlink_to(outside)
        with mock.patch.dict(os.environ,self.env), self.assertRaises(ValueError):
            with Runtime(control):pass
        self.assertEqual(outside.read_bytes(),b'unchanged')
        (control/'engine.sock').unlink()  # Only link made by this controlled test.
        credential=(control/'client.json').read_bytes();(control/'client.json').chmod(0o644)
        with mock.patch.dict(os.environ,self.env), self.assertRaises(Refused):call(control,'status')
        (control/'client.json').chmod(0o600)
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            pair=self.pairing();params=self.params(pair)
            with contextlib.closing(sqlite3.connect(control/'requests.sqlite3')) as db,db:
                for i in range(256):db.execute('INSERT INTO requests VALUES(?,?,?,?,\'RECEIVED\',NULL)',(str(i),'app','digest',None))
            self.assertEqual(call(control,'quick_join',params)['error'],'request_limit')
            self.assertFalse((root/'node/enrollment_pending.json').exists())
        self.assertEqual((control/'client.json').read_bytes(),credential)

    def test_actual_lost_unix_success_reply_replays_durable_receipt(self):
        root=self.fresh();control=self.control(root);pair=self.pairing();params=self.params(pair)
        rid='11111111-1111-4111-8111-111111111111'
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            auth=json.loads((control/'client.json').read_bytes())
            value=dict(api_version=1,request_id=rid,app_id=auth['app_id'],authorization=auth['authorization'],operation='quick_join',params=params)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.connect(str(control/'engine.sock'));connection.sendall(json.dumps(value).encode()+b'\n')
                connection.shutdown(socket.SHUT_RDWR)  # Drop the actual response, not a fabricated success.
            def done():
                with contextlib.closing(sqlite3.connect(control/'requests.sqlite3')) as db:
                    row=db.execute('SELECT state FROM requests WHERE request_id=?',(rid,)).fetchone()
                    return row and row[0]=='DONE'
            self.wait_for(done)
            cfg=(root/'node/node.json').read_bytes()
            reply=call(control,'quick_join',{k:v for k,v in params.items() if k!='code'},rid);self.assertTrue(reply['replayed'])
            self.assertEqual((root/'node/node.json').read_bytes(),cfg)
            with contextlib.closing(sqlite3.connect(control/'requests.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM requests').fetchone()[0],1)

    def test_protected_unknown_and_state_root_replacement_preserve_identity(self):
        root=self.fresh();control=self.control(root);marker=(root/'demo.json').read_bytes()
        for model in ('SM-M515F','unknown',''):
            env=dict(self.env,ASC_TEST_MODEL=model)
            with mock.patch.dict(os.environ,env), self.assertRaises(ValueError):provision(self.home/'must-not-create',root)
            self.assertFalse((self.home/'must-not-create').exists());self.assertEqual((root/'demo.json').read_bytes(),marker)
            with mock.patch.dict(os.environ,env), mock.patch('asc.bridge.service.private.directory',side_effect=AssertionError('must guard before private access')), self.assertRaises(ValueError):
                Runtime(control)
        with mock.patch.dict(os.environ,self.env), Runtime(control):
            retained=root.with_name('retained-original-state');root.rename(retained)
            root.mkdir(mode=0o700);(root/'demo.json').write_bytes(marker)
            self.assertFalse(call(control,'status')['ok'])
            self.assertEqual((retained/'demo.json').read_bytes(),marker)
