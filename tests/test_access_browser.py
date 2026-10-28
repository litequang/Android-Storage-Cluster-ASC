"""Actual existing mobile/PWA browser workflow through the private ingress."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import unittest
from tests import test_access_gateway as fixture


class PrivateGatewayBrowserTests(unittest.TestCase):
    def setUp(self):
        for name in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(name),'actual browser tool required; never skip TLS gates')
        self.f=fixture.PrivateGatewayTests();self.addCleanup(self.f.doCleanups);self.f.setUp()

    def test_actual_chromium_owner_files_pwa_sha_fallback_and_network_loss(self):
        backend=self.f.f;out=Path(self.f.temp.name)/'browser';out.mkdir(mode=0o700)
        grant=backend.command(backend.controller,'dashboard-code')
        config={'pwa':True,'origin':self.f.origin,'code':grant['code'],'ca':str(self.f.root/'dashboard/ca.crt'),
            'payload':str(backend.payload),'sha':hashlib.sha256(backend.data).hexdigest(),'output':str(out),
            'logical':'private-browser/<img src=x onerror=globalThis.dashboardXss=1>.bin'}
        child=subprocess.Popen(['node',str(backend.repo/'tests/browser/demo_dashboard.cjs')],cwd=backend.repo,
            env=backend.env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def cleanup():
            if child.poll() is None:child.terminate();child.wait(timeout=15)
            for pipe in (child.stdin,child.stdout,child.stderr):
                if not pipe.closed:pipe.close()
        self.addCleanup(cleanup);child.stdin.write(json.dumps(config));child.stdin.close()
        stopped=False;deadline=time.monotonic()+150
        while child.poll() is None and time.monotonic()<deadline:
            if (out/'stop-node.json').exists() and not stopped:
                node_id=json.loads((out/'stop-node.json').read_text())['node_id']
                backend.stop(next(n for n in backend.nodes if n['cfg']['node_id']==node_id)['process'])
                (out/'node-stopped').write_text('actual owned synthetic node stopped');stopped=True
            time.sleep(.1)
        if child.poll() is None:child.terminate();self.fail('original150s actual browser deadline')
        raw,errors=child.stdout.read(),child.stderr.read()
        self.assertEqual(child.returncode,0,errors);reply=json.loads(raw)
        self.assertTrue(reply['passed']);self.assertTrue(stopped);self.assertEqual(reply['replicas'],2)
        self.assertTrue(reply['trusted_tls']);self.assertTrue(reply['untrusted_tls_denied'])
        self.assertTrue(reply['offline_refused']);self.assertEqual(reply['page_errors'],0)
        self.assertEqual(reply['sha256'],hashlib.sha256(backend.data).hexdigest())
        self.assertEqual((out/'downloaded-after-node-offline.bin').read_bytes(),backend.data)
        destination=Path(getattr(self.f,'artifact_directory','/workspace/work/phase5-private-browser'));destination.mkdir(mode=0o700,exist_ok=True)
        for name in ('dashboard-desktop.png','dashboard-mobile.png'):shutil.copyfile(out/name,destination/name)
        (destination/'result.json').write_text(json.dumps(reply,indent=2)+'\n')
