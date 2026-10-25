"""Actual owned Node lifecycle/bridge SIGKILL/socket receipt, synthetic bytes only."""
import hashlib
import http.server
import ssl
import threading
import sqlite3
import contextlib
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from unittest import mock
from asc.bridge.service import Runtime, call
from asc.bridge.contract import Refused
from asc.runtime import running
from tests import test_bridge as fixture
from tests import test_quick_join as quick


class HeldSuccessfulJoin(quick.JoinProxy):
    def send_response(self,code,message=None):
        self.status_code=code;return super().send_response(code,message)
    def end_headers(self):
        if self.path=='/api/v1/join' and self.status_code==201:
            self.server.arrived.set()
            if not self.server.release.wait(12):raise RuntimeError('Synthetic ACK hold timed out')
        return super().end_headers()


class BridgeLifecycleTests(unittest.TestCase):
    script=fixture.BridgeTests.script
    run_cli=fixture.BridgeTests.run_cli
    free_port=staticmethod(fixture.BridgeTests.free_port)
    command_result=fixture.BridgeTests.command_result
    command=fixture.BridgeTests.command
    stop=fixture.BridgeTests.stop
    wait_for=fixture.BridgeTests.wait_for
    seen=fixture.BridgeTests.seen
    admin=fixture.BridgeTests.admin
    upload=fixture.BridgeTests.upload
    start=fixture.BridgeTests.start
    login=fixture.BridgeTests.login
    http=fixture.BridgeTests.http
    setUp=fixture.BridgeTests.setUp
    control=fixture.BridgeTests.control

    def agent_running(self,root):
        with mock.patch.dict(os.environ,self.env):return running(root/'node','agent')

    def test_controlled_existing_node_restart_preserves_bytes_and_never_stops_foreign_process(self):
        entry=self.upload();root=self.bphone
        cfg=(root/'node/node.json').read_bytes()
        self.stop(self.nodes[1]['process']);control=self.control(root,('read','lifecycle'))
        with mock.patch.dict(os.environ,self.env), Runtime(control) as runtime:
            rid='11111111-1111-4111-8111-111111111111'
            result=call(control,'node_start',request_id=rid);self.assertTrue(result['ok'],result)
            self.wait_for(lambda:self.agent_running(root) is True)
            process=runtime.bridge.lifecycle.process
            self.assertIsNone(process.poll())
            replay=call(control,'node_start',request_id=rid);self.assertTrue(replay['historical_receipt'])
            self.assertIs(runtime.bridge.lifecycle.process,process)
            status=call(control,'status')['result'];self.assertTrue(status['owned_node']['owned'])
            self.assertIsNone(status['volumes'][0]['writable']);self.assertIsNone(status['owned_node']['storage_ready'])
            self.wait_for(lambda:self.command(self.controller,'replicas',entry['file']['file_id'])['available_replicas']==2)
            target=self.home/'owned-node-download';self.command(self.controller,'download',entry['file']['file_id'],str(target))
            self.assertEqual(hashlib.sha256(target.read_bytes()).digest(),hashlib.sha256(self.data).digest())
            stopped=call(control,'node_stop',request_id='22222222-2222-4222-8222-222222222222')
            self.assertEqual(stopped['result']['state'],'STOPPED');self.assertIsNotNone(process.poll())
            self.assertEqual((root/'node/node.json').read_bytes(),cfg)
            # A foreign actual foreground may run afterward; bridge must not kill it.
            foreign=self.start(root,'run-node');self.wait_for(lambda:self.agent_running(root) is True)
            self.assertEqual(call(control,'node_start')['error'],'external_runtime_owned')
            self.assertEqual(call(control,'node_stop')['result']['state'],'NO_OWNED_NODE')
            self.assertIsNone(foreign.poll())
            with self.assertRaises(Refused):call(control,'node_stop',{'pid':foreign.pid})

    def process_bridge(self,control):
        process=subprocess.Popen([sys.executable,'-B','-m','asc.bridge.cli','--control',str(control),'run'],
            cwd=self.repo,env=self.env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop,process)
        def active():
            try:
                with mock.patch.dict(os.environ,self.env):return call(control,'status')['ok']
            except (OSError,ValueError):return False
        self.wait_for(active);return process

    def test_actual_bridge_sigkill_parent_death_and_exact_socket_recovery_no_autostart(self):
        entry=self.upload();root=self.bphone;self.stop(self.nodes[1]['process'])
        control=self.control(root,('read','lifecycle'));cfg=(root/'node/node.json').read_bytes()
        process=self.process_bridge(control);rid='11111111-1111-4111-8111-111111111111'
        with mock.patch.dict(os.environ,self.env):self.assertTrue(call(control,'node_start',request_id=rid)['ok'])
        self.wait_for(lambda:self.agent_running(root) is True)
        process.kill();process.wait(timeout=10)  # Actual SIGKILL of only this synthetic bridge.
        self.wait_for(lambda:self.agent_running(root) is False)
        self.assertTrue((control/'engine.sock').exists());self.assertEqual((root/'node/node.json').read_bytes(),cfg)
        restarted=self.process_bridge(control)
        with mock.patch.dict(os.environ,self.env):
            self.assertFalse(call(control,'status')['result']['owned_node']['owned'])
            self.assertTrue(call(control,'node_start',request_id=rid)['historical_receipt'])
            self.assertFalse(self.agent_running(root),'historical receipt never auto-starts')
            self.assertTrue(call(control,'node_start',request_id='22222222-2222-4222-8222-222222222222')['ok'])
        self.wait_for(lambda:self.agent_running(root) is True)
        self.wait_for(lambda:self.command(self.controller,'replicas',entry['file']['file_id'])['available_replicas']==2)
        target=self.home/'after-bridge-crash';self.command(self.controller,'download',entry['file']['file_id'],str(target))
        self.assertEqual(target.read_bytes(),self.data);self.assertEqual((root/'node/node.json').read_bytes(),cfg)
        self.stop(restarted);self.wait_for(lambda:self.agent_running(root) is False)

    def test_installed_verified_launcher_bridge_status_and_wrong_root_refusal(self):
        prefix=self.home/'bridge-installed-code';root=self.home/'installed-node'
        self.assertEqual(self.run_cli('install','--prefix',str(prefix)).returncode,0)
        command=['sh',str(prefix/'bin/asc-demo'),'--state',str(root)]
        def invoke(*args):return subprocess.run([*command,*args],cwd=self.root,env=self.env,capture_output=True,text=True,timeout=30)
        self.assertEqual(invoke('init','--role','node','--host','127.0.0.1').returncode,0)
        control=self.home/'installed-control'
        self.assertEqual(invoke('bridge-provision','--control',str(control),'--allow-join').returncode,0)
        process=subprocess.Popen([*command,'bridge-run','--control',str(control)],cwd=self.root,env=self.env,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop,process)
        self.wait_for(lambda:(control/'engine.sock').exists())
        reply=invoke('bridge-status','--control',str(control))
        self.assertEqual(reply.returncode,0,'Installed bridge refused; private output suppressed')
        self.assertFalse(json.loads(reply.stdout)['result']['node']['identity_present'])
        before=(root/'demo.json').read_bytes()
        # Installed prefix/root binding is checked by existing launcher path.
        other=subprocess.run(['sh',str(prefix/'bin/asc-demo'),'--state',str(self.bphone),'bridge-status','--control',str(control)],
            cwd=self.root,env=self.env,capture_output=True,text=True,timeout=30)
        self.assertNotEqual(other.returncode,0);self.assertEqual((root/'demo.json').read_bytes(),before)
        with mock.patch.dict(os.environ,self.env):self.assertEqual(call(control,'node_start')['error'],'scope_denied')

    def test_bridge_crash_after_actual_join_commit_resumes_original_pending_identity(self):
        root=self.home/'join-crash-node';self.command(root,'init','--role','node','--host','127.0.0.1')
        control=self.control(root,('read','join'));pair=fixture.BridgeTests.pairing(self)
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),HeldSuccessfulJoin)
        server.origin=self.origin;server.pin=self.pin;server.drop=False;server.dropped=False;server.override=None;server.join_calls=0
        server.arrived=threading.Event();server.release=threading.Event()
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.controller/'controller/server.crt',self.controller/'controller/server.key')
        server.socket=context.wrap_socket(server.socket,server_side=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(lambda:(server.release.set(),server.shutdown(),server.server_close(),thread.join(timeout=10)))
        params=fixture.BridgeTests.params(self,pair);params['controller']='https://127.0.0.1:'+str(server.server_address[1])
        process=self.process_bridge(control);rid='11111111-1111-4111-8111-111111111111'
        with mock.patch.dict(os.environ,self.env), ThreadPoolExecutor(max_workers=1) as pool:
            reply=pool.submit(call,control,'quick_join',params,rid)
            self.assertTrue(server.arrived.wait(10),'Actual successful Controller201 must reach paused TLS ACK')
            pending=json.loads((root/'node/enrollment_pending.json').read_bytes())
            process.kill();process.wait(timeout=10)
            with self.assertRaises((OSError,Refused)):reply.result(timeout=10)
            server.release.set()
            self.wait_for(lambda:(root/'node/node.json').exists())
            cfg=json.loads((root/'node/node.json').read_bytes())
            self.assertEqual(cfg['token'],pending['payload']['enrollment_token'])
            restarted=self.process_bridge(control)
            result=call(control,'quick_join',{k:v for k,v in params.items() if k!='code'},rid)
            self.assertTrue(result['ok']);self.assertEqual(result['result']['node_id'],cfg['node_id'])
            self.assertEqual(result['result']['controller_confirmation'],'unknown')
            self.assertEqual(server.join_calls,1,'No duplicate enrollment after bridge death and committed receipt')
            with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM enrollments WHERE node_id=?',(cfg['node_id'],)).fetchone()[0],1)
            self.assertFalse((root/'node/storage.json').exists());self.stop(restarted)
