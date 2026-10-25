"""Actual pinned TLS/session/CLI enrollment; no phone, mock success or second DB."""
import contextlib
import hashlib
import http.client
import http.server
import json
from pathlib import Path
import socket
import sqlite3
import ssl
import subprocess
import threading
import time
import unittest
from unittest import mock

from asc.client import connect_pinned, request_json
from asc.demo.pairing import PairingError, Pairings
from tests import test_demo_dashboard as fixture


class JoinProxy(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def relay(self):
        connection=connect_pinned(self.server.origin,self.server.pin,timeout=20)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<=size<=65536:raise ValueError()
            data=self.rfile.read(size) if size else None
            connection.request(self.command,self.path,data,{'Content-Type':'application/json'})
            response=connection.getresponse();raw=response.read(2*1024**2)
            if self.path=='/api/v1/join':
                self.server.join_calls+=1
                if self.server.drop and response.status==201:
                    self.server.drop=False;self.server.dropped=True;self.close_connection=True;return
            if self.path=='/api/v1/info' and self.server.override:
                info=json.loads(raw);info.update(self.server.override);raw=json.dumps(info).encode()
            self.send_response(response.status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)));self.send_header('Connection','close');self.end_headers()
            self.wfile.write(raw);self.close_connection=True
        finally:connection.close()
    do_GET=do_POST=relay


class QuickJoinTests(unittest.TestCase):
    script=fixture.DashboardAPITests.script
    run_cli=fixture.DashboardAPITests.run_cli
    free_port=staticmethod(fixture.DashboardAPITests.free_port)
    command_result=fixture.DashboardAPITests.command_result
    command=fixture.DashboardAPITests.command
    stop=fixture.DashboardAPITests.stop
    wait_for=fixture.DashboardAPITests.wait_for
    seen=fixture.DashboardAPITests.seen
    admin=fixture.DashboardAPITests.admin
    upload=fixture.DashboardAPITests.upload
    start=fixture.DashboardAPITests.start
    login=fixture.DashboardAPITests.login
    http=fixture.DashboardAPITests.http
    setUp=fixture.DashboardAPITests.setUp

    def pairing(self):
        status,_,reply=self.http('POST','/api/v1/quick-join/pairings',{})
        self.assertEqual(status,201,reply);self.assertEqual(reply['quick_join_version'],1)
        return reply

    def status(self,pair):
        status,_,reply=self.http('GET','/api/v1/quick-join/pairings/'+pair['pairing_id'])
        self.assertEqual(status,200,reply);return reply

    def fresh(self,label='quick-phone'):
        root=self.home/label
        self.command(root,'init','--role','node','--host','127.0.0.1')
        return root

    def join(self,root,pair,**kwargs):
        args=['quick-join','--controller',kwargs.pop('origin',pair['controller']),
            '--pin',kwargs.pop('pin',pair['pin']),'--expected-cluster-id',kwargs.pop('cluster',pair['cluster_id']),
            '--name','Quick Join synthetic']
        if kwargs.pop('new_code',False):args+=['--new-code']
        return self.command_result(root,*args,input=pair['code']+'\n')

    def proxy(self,drop=False,override=None):
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),JoinProxy)
        server.origin=self.origin
        server.pin=self.pin;server.drop=drop;server.dropped=False;server.override=override;server.join_calls=0
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.controller/'controller/server.crt',self.controller/'controller/server.key')
        server.socket=context.wrap_socket(server.socket,server_side=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(lambda:(server.shutdown(),server.server_close(),thread.join(timeout=10)))
        return server,'https://127.0.0.1:'+str(server.server_address[1])

    def test_owner_session_csrf_scope_bounds_and_no_secret_status(self):
        self.assertEqual(self.http('POST','/api/v1/quick-join/pairings',{},authenticated=False)[0],401)
        self.assertEqual(self.http('POST','/api/v1/quick-join/pairings',{},headers={'Origin':'https://attacker.invalid'})[0],403)
        self.assertEqual(self.http('POST','/api/v1/quick-join/pairings',{},headers={'X-ASC-CSRF':''})[0],401)
        self.assertEqual(self.http('POST','/api/v1/quick-join/pairings',{'node_id':'forbidden-repair'})[0],400)
        pair=self.pairing();self.assertEqual(self.status(pair)['state'],'waiting')
        safe=json.dumps(self.status(pair))
        for secret in (pair['code'],self.admin(),self.nodes[0]['cfg']['token'],self.csrf):self.assertNotIn(secret,safe)
        old_cookie,old_csrf=self.cookie,self.csrf
        self.login();self.assertEqual(self.http('GET','/api/v1/quick-join/pairings/'+pair['pairing_id'])[0],404)
        self.cookie,self.csrf=old_cookie,old_csrf
        for _ in range(7):self.pairing()
        self.assertEqual(self.http('POST','/api/v1/quick-join/pairings',{})[0],429)
        self.assertEqual(self.http('POST','/api/logout',{})[0],200)
        self.assertEqual(self.http('GET','/api/v1/quick-join/pairings/'+pair['pairing_id'])[0],401)

    def test_real_guided_join_does_not_approve_storage_and_reinstall_retains_identity(self):
        pair=self.pairing();root=self.fresh();result=self.join(root,pair)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(result.stdout);self.assertEqual(report['state'],'registered')
        cfg=json.loads((root/'node/node.json').read_bytes())
        self.assertEqual(report['node_id'],cfg['node_id'])
        state=self.status(pair);self.assertEqual(state['state'],'registered')
        self.assertFalse(state['storage_approved']);self.assertIsNone(state['failure_domain'])
        self.assertFalse((root/'node/storage.json').exists());self.assertFalse((root/'node/storage/manifest.sqlite3').exists())
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes WHERE node_id=?',(cfg['node_id'],)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM nodes WHERE node_id!=?',('local-controller',)).fetchone()[0],3)
        before=(root/'node/node.json').read_bytes()
        again=self.join(root,pair);self.assertEqual(again.returncode,0)
        self.assertEqual(json.loads(again.stdout)['controller_confirmation'],'unknown')
        self.assertEqual((root/'node/node.json').read_bytes(),before)
        for secret in (cfg['token'],pair['code'],self.admin()):self.assertNotIn(secret,result.stdout+result.stderr)
        request_json(self.origin,self.pin,'POST','/api/v1/admin/revoke',{'node_id':cfg['node_id']},self.admin())
        self.assertEqual(self.status(pair)['state'],'revoked')

    def test_actual_successful_join_ack_lost_then_same_pending_operation_resumes(self):
        pair=self.pairing();root=self.fresh();proxy,origin=self.proxy(drop=True)
        failed=self.join(root,pair,origin=origin)
        self.assertNotEqual(failed.returncode,0);self.assertTrue(proxy.dropped,'must lose actual successful201 join response')
        pending=root/'node/enrollment_pending.json';self.assertTrue(pending.exists());self.assertFalse((root/'node/node.json').exists())
        operation=json.loads(pending.read_bytes());payload=operation['payload']
        self.assertEqual(json.loads(failed.stdout)['state'],'resume_required')
        tracked=self.status(pair);self.assertEqual(tracked['state'],'registered')
        resumed=self.join(root,pair,origin=origin);self.assertEqual(resumed.returncode,0,resumed.stdout+resumed.stderr)
        cfg=json.loads((root/'node/node.json').read_bytes());self.assertEqual(cfg['node_id'],tracked['node_id'])
        self.assertEqual(cfg['token'],payload['enrollment_token']);self.assertFalse(pending.exists())
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM enrollments WHERE node_id=?',(cfg['node_id'],)).fetchone()[0],1)
        self.assertEqual(proxy.join_calls,2)

    def test_expired_code_replacement_keeps_original_private_operation(self):
        pair=self.pairing();root=self.fresh()
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db,db:
            db.execute('UPDATE join_codes SET expires_at=? WHERE code_hash=?',(int(time.time())-1,hashlib.sha256(pair['code'].encode()).hexdigest()))
        self.assertEqual(self.status(pair)['state'],'expired')
        failed=self.join(root,pair);self.assertNotEqual(failed.returncode,0)
        path=root/'node/enrollment_pending.json';before=json.loads(path.read_bytes())
        fresh=self.pairing();resumed=self.join(root,fresh,new_code=True)
        self.assertEqual(resumed.returncode,0,resumed.stdout+resumed.stderr)
        cfg=json.loads((root/'node/node.json').read_bytes());self.assertEqual(cfg['token'],before['payload']['enrollment_token'])
        self.assertEqual(self.status(fresh)['node_id'],cfg['node_id'])
        abandoned=next((root/'node').glob('enrollment_abandoned-*.json'))
        self.assertEqual(json.loads(abandoned.read_bytes())['payload']['enrollment_id'],before['payload']['enrollment_id'])

    def test_pin_cluster_quorum_mode_and_recovery_staging_refuse_before_pending(self):
        pair=self.pairing();root=self.fresh()
        for kwargs,error in (({'pin':'0'*64},'tls_pin_mismatch'),({'cluster':'11111111-1111-4111-8111-111111111111'},'cluster_mismatch')):
            result=self.join(root,pair,**kwargs);self.assertNotEqual(result.returncode,0)
            self.assertEqual(json.loads(result.stdout)['error'],error);self.assertFalse((root/'node/enrollment_pending.json').exists())
        proxy,origin=self.proxy(override={'mode':'distributed-runtime-development','raft_enabled':True})
        result=self.join(root,pair,origin=origin);self.assertNotEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)['error'],'unsupported_runtime');self.assertEqual(proxy.join_calls,0)
        (root/'RECOVERY_READ_ONLY.json').write_text('{"writer_authority":false}')
        before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        result=self.join(root,pair);self.assertNotEqual(result.returncode,0)
        self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})
        self.assertFalse((root/'node/node.json').exists())

    def test_competing_operations_one_use_and_exact_original_retry(self):
        import concurrent.futures,secrets
        pair=self.pairing()
        values=[{'code':pair['code'],'name':'competing-'+str(i),'profile':{'protected':False},
            'enrollment_id':secrets.token_urlsafe(32),'enrollment_token':secrets.token_urlsafe(32)} for i in range(2)]
        def attempt(payload):
            try:return request_json(self.origin,self.pin,'POST','/api/v1/join',payload)
            except Exception as exc:
                from asc.client import ClientError
                if not isinstance(exc,ClientError):raise
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,values))
        self.assertEqual(sum(r is not None for r in results),1)
        winner=next(i for i,r in enumerate(results) if r is not None)
        retry=attempt(values[winner]);self.assertEqual(retry['node_id'],results[winner]['node_id'])
        self.assertFalse(self.status(pair)['storage_approved'])

    def test_restart_loses_browser_tracking_but_pending_node_identity_can_resume(self):
        pair=self.pairing();root=self.fresh();self.stop(self.controller_process)
        failed=self.join(root,pair);self.assertNotEqual(failed.returncode,0)
        self.assertFalse((root/'node/enrollment_pending.json').exists(),'no trusted server info => no enrollment operation or code submission')
        self.controller_process=self.start(self.controller,'run-controller')
        self.wait_for(lambda:request_json(self.origin,self.pin,'GET','/api/v1/info'))
        self.login();self.assertEqual(self.http('GET','/api/v1/quick-join/pairings/'+pair['pairing_id'])[0],404)
        resumed=self.join(root,pair);self.assertEqual(resumed.returncode,0,resumed.stdout+resumed.stderr)
        self.assertTrue((root/'node/node.json').exists(),'restart does not revoke persisted unconsumed600s Core code')


    def test_global_pairing_bound_and_non_demo_backend_never_adopted(self):
        self.http('POST','/api/logout',{})
        for _ in range(4):
            self.login()
            for _ in range(8):self.pairing()
        self.login();self.assertEqual(self.http('POST','/api/v1/quick-join/pairings',{})[0],429)
        from types import SimpleNamespace
        with self.assertRaises(PairingError) as denied:
            Pairings(self.controller,SimpleNamespace(failover=True),None)
        self.assertEqual(denied.exception.code,'unsupported_runtime')

    def test_missing_setup_protected_and_unknown_devices_never_initialize_identity(self):
        pair=self.pairing();root=self.home/'uninitialized-quick-node'
        result=self.join(root,pair);self.assertNotEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)['error'],'setup_required');self.assertFalse(root.exists())
        for model in ('SM-M515F','unknown',''):
            self.env['ASC_TEST_MODEL']=model
            result=self.join(root,pair);self.assertNotEqual(result.returncode,0)
            self.assertFalse(root.exists())
