"""Fresh actual owner browser approval -> two real replicas -> fallback/revoke."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import unittest

from asc.client import request_json
from tests import test_demo_dashboard as fixture
from tests.test_dashboard_management import pending_node


class ManagementBrowserTests(unittest.TestCase):
    def test_mobile_owner_management_real_storage_bytes_fallback_and_revoke(self):
        for executable in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(executable), 'Browser prerequisite required; never skip')
        f=fixture.DashboardAPITests(); self.addCleanup(f.doCleanups); f.setUp()
        added=pending_node(f); node_id=added['cfg']['node_id']
        # Leave exactly two eligible logical domains after the new web approval.
        disabled=f.nodes[1]
        request_json(f.origin,f.pin,'POST','/catalog/v1/nodes/register',
            dict(node_id=disabled['cfg']['node_id'],device_id='phone-1',volume_ids=[],storage_allowed=False),f.admin())
        output=f.root/'management-browser';output.mkdir(mode=0o700)
        grant=f.command(f.controller,'dashboard-code')
        config=dict(origin=f.browser_origin,code=grant['code'],ca=str(f.controller/'dashboard/ca.crt'),
            node_id=node_id,volume_id=added['volume'],node_origin='https://127.0.0.1:'+str(added['port']),
            node_pin=added['pin'],payload=str(f.payload),sha256=hashlib.sha256(f.data).hexdigest(),output=str(output))
        process=subprocess.Popen(['node',str(f.repo/'tests/browser/dashboard_management.cjs')],cwd=f.repo,env=f.env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.addCleanup(lambda:process.kill() if process.poll() is None else None)
        process.stdin.write(json.dumps(config));process.stdin.close()
        stopped=False;before=None;deadline=time.monotonic()+180
        while process.poll() is None and time.monotonic()<deadline:
            signal=output/'stop-node.json'
            if signal.exists() and not stopped:
                self.assertEqual(json.loads(signal.read_bytes())['node_id'],node_id)
                before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (added['root']/'node/data/objects').glob('*.blob')}
                self.assertTrue(before,'Web-approved real Node must actually store replica bytes')
                f.stop(added['process']);stopped=True;(output/'node-stopped').write_text('owned actual Node stopped')
            time.sleep(.1)
        if process.poll() is None:process.kill()
        process.wait(timeout=10)
        stdout,stderr=process.stdout.read(),process.stderr.read();process.stdout.close();process.stderr.close()
        self.assertEqual(process.returncode,0,stderr)
        self.assertTrue(json.loads(stdout)['passed']);self.assertTrue(stopped)
        self.assertEqual((output/'fallback.bin').read_bytes(),f.data)
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (added['root']/'node/data/objects').glob('*.blob')}
        self.assertEqual(after,before)
        review=Path('/workspace/work/dashboard-browser');review.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'management-mobile.png',review/'management-mobile.png')


if __name__ == '__main__':
    unittest.main()
