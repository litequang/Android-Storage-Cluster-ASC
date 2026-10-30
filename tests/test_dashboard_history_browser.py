"""Trusted real mobile browser snapshot pause/offline/resume/restore, actual bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import unittest
from tests import test_demo_dashboard as fixture
from tests import test_dashboard_files as files
from asc.client import connect_pinned


class HistoryBrowserTests(unittest.TestCase):
    def test_actual_snapshot_pause_node_offline_resume_restore_and_sha(self):
        for executable in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(executable),'Real trusted browser gate; never skip')
        f=fixture.DashboardAPITests();self.addCleanup(f.doCleanups);f.setUp()
        helper=files.FileManagerTests();helper.f=f
        first=helper.upload(f.data,1,'history_browser_v1','history-browser/report.bin')
        helper.upload(b'second version',2,'history_browser_v2','history-browser/report.bin')
        helper.upload(b'third version',3,'history_browser_v3','history-browser/report.bin')
        grant=f.command(f.controller,'dashboard-code');output=f.root/'history-browser';output.mkdir(mode=0o700)
        cfg=dict(origin=f.browser_origin,ca=str(f.controller/'dashboard/ca.crt'),code=grant['code'],
            output=str(output),first=first,sha256=hashlib.sha256(f.data).hexdigest())
        process=subprocess.Popen(['node',str(f.repo/'tests/browser/dashboard_history.cjs')],cwd=f.repo,env=f.env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.addCleanup(lambda:process.kill() if process.poll() is None else None)
        process.stdin.write(json.dumps(cfg));process.stdin.close();stopped=False;restarted=False;deadline=time.monotonic()+180
        while process.poll() is None and time.monotonic()<deadline:
            if (output/'stop-node').exists() and not stopped:
                f.stop(f.nodes[0]['process']);stopped=True;(output/'node-stopped').write_text('actual test Node stopped')
            if (output/'restart-node').exists() and stopped and not restarted:
                f.nodes[0]['process']=f.start(f.nodes[0]['root'],'run-node');restarted=True
                def ready():
                    self.assertIsNone(f.nodes[0]['process'].poll(),'Owned Node exited during restart')
                    connection=connect_pinned('https://127.0.0.1:'+str(f.nodes[0]['port']),f.nodes[0]['pin'],timeout=1)
                    connection.close();return True
                f.wait_for(ready)  # Spawned PID is not a ready TLS/Storage listener.
                (output/'node-restarted').write_text('actual retained test Node restarted')
            time.sleep(.1)
        if process.poll() is None:process.kill();process.wait();self.fail('Real history browser deadline; no simulated success')
        stderr,stdout=process.stderr.read(),process.stdout.read();process.stdout.close();process.stderr.close()
        self.assertEqual(process.returncode,0,stderr);self.assertTrue(json.loads(stdout)['passed'])
        self.assertTrue(stopped and restarted);self.assertEqual((output/'restored.bin').read_bytes(),f.data)
        review=Path('/workspace/work/dashboard-browser');review.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'history-mobile.png',review/'history-mobile.png')


if __name__=='__main__':unittest.main()
