"""Real mobile preferences persistence, measured health and redacted JSON export."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from tests import test_demo_dashboard as fixture


class DiagnosticBrowserTests(unittest.TestCase):
    def test_actual_owner_preferences_reload_measured_fsync_and_diagnostic_download(self):
        for tool in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(tool),'Required real trusted browser gate; never skip')
        f=fixture.DashboardAPITests();self.addCleanup(f.doCleanups);f.setUp();f.upload()
        grant=f.command(f.controller,'dashboard-code');output=f.root/'diagnostic-browser';output.mkdir(mode=0o700)
        cfg=dict(origin=f.browser_origin,ca=str(f.controller/'dashboard/ca.crt'),code=grant['code'],output=str(output))
        run=subprocess.run(['node',str(f.repo/'tests/browser/dashboard_diagnostics.cjs')],cwd=f.repo,env=f.env,
            input=json.dumps(cfg),capture_output=True,text=True,timeout=100)
        self.assertEqual(run.returncode,0,run.stderr);self.assertTrue(json.loads(run.stdout)['passed'])
        raw=(output/'asc-diagnostics.json').read_text()
        for secret in (f.admin(),f.nodes[0]['cfg']['token'],f.nodes[0]['cfg']['node_id'],str(f.controller),f.origin,f.pin,'demo/real.bin'):
            self.assertNotIn(secret,raw)
        report=json.loads(raw);self.assertEqual(report['counts']['files'],1);self.assertEqual(report['diagnostic_api_version'],1)
        self.assertTrue(all(v['fsync_tested'] is True for n in report['nodes'] for v in n['volumes']))
        review=Path('/workspace/work/dashboard-browser');review.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'diagnostics-mobile.png',review/'diagnostics-mobile.png')


if __name__=='__main__':unittest.main()
