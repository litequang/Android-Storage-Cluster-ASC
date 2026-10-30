"""Real browser bootstrap/password/account roles over canonical two-node TLS cluster."""
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import unittest
from tests import test_demo_dashboard as fixture


class AccountBrowserTests(unittest.TestCase):
    def test_actual_mobile_owner_password_viewer_download_and_rotation(self):
        for tool in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(tool),'Required real browser gate; never skip')
        f=fixture.DashboardAPITests();self.addCleanup(f.doCleanups);f.setUp()
        entry=f.upload();grant=f.command(f.controller,'dashboard-code')
        output=f.root/'account-browser';output.mkdir(mode=0o700)
        cfg=dict(origin=f.browser_origin,ca=str(f.controller/'dashboard/ca.crt'),code=grant['code'],
            owner_password=secrets.token_urlsafe(24),viewer_password=secrets.token_urlsafe(24),rotated_password=secrets.token_urlsafe(24),
            file_id=entry['file']['file_id'],sha256=hashlib.sha256(f.data).hexdigest(),output=str(output))
        run=subprocess.run(['node',str(f.repo/'tests/browser/dashboard_accounts.cjs')],cwd=f.repo,env=f.env,
            input=json.dumps(cfg),capture_output=True,text=True,timeout=160)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertTrue(json.loads(run.stdout)['passed']);self.assertEqual((output/'viewer.bin').read_bytes(),f.data)
        review=Path('/workspace/work/dashboard-browser');review.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'accounts-viewer-mobile.png',review/'accounts-viewer-mobile.png')


if __name__=='__main__':unittest.main()
