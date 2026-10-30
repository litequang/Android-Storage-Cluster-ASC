"""Actual mobile browser file pagination, logical navigation and immutable versions."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from asc.client import request_json
from tests import test_demo_dashboard as fixture


class FileBrowserTests(unittest.TestCase):
    def test_actual_browser_pagination_folder_version_upload_history_and_old_sha(self):
        for tool in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(tool),'Required real browser gate; never skip')
        f=fixture.DashboardAPITests();self.addCleanup(f.doCleanups);f.setUp()
        for i in range(53):
            request_json(f.origin,f.pin,'POST','/catalog/v1/uploads',dict(logical_path=f'listing/item-{i:03d}.txt',
                size=4,sha256=hashlib.sha256(b'data').hexdigest(),version=1,policy='replicated_2',idempotency_key='browser_listing_'+str(i).zfill(8)),f.admin())
        second=f.root/'second.bin';second.write_bytes(b'new immutable content, old version stays readable')
        output=f.root/'file-browser';output.mkdir(mode=0o700)
        grant=f.command(f.controller,'dashboard-code')
        cfg=dict(origin=f.browser_origin,ca=str(f.controller/'dashboard/ca.crt'),code=grant['code'],
            first=str(f.payload),second=str(second),sha256=hashlib.sha256(f.data).hexdigest(),
            second_sha256=hashlib.sha256(second.read_bytes()).hexdigest(),output=str(output))
        run=subprocess.run(['node',str(f.repo/'tests/browser/dashboard_files.cjs')],cwd=f.repo,env=f.env,
            input=json.dumps(cfg),capture_output=True,text=True,timeout=180)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertTrue(json.loads(run.stdout)['passed']);self.assertEqual((output/'old-version.bin').read_bytes(),f.data)
        review=Path('/workspace/work/dashboard-browser');review.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'files-mobile.png',review/'files-mobile.png')


if __name__=='__main__':unittest.main()
