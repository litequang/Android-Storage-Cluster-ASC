"""Trusted Chromium owner UI -> actual CLI node; no certificate bypass or phones."""
import contextlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
import unittest
from tests import test_quick_join as fixture


class QuickJoinBrowserTests(unittest.TestCase):
    # Reuse fixture helpers without rediscovering/inheriting its test cases.
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
    fresh=fixture.QuickJoinTests.fresh
    join=fixture.QuickJoinTests.join

    def setUp(self):
        for executable in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(executable),'Required browser gate unavailable; never skip')
        fixture.QuickJoinTests.setUp(self)

    def test_owner_browser_guides_actual_cli_without_approval_or_persistent_code(self):
        output=self.root/'quick-browser';output.mkdir(mode=0o700)
        node=self.fresh();grant=self.command(self.controller,'dashboard-code')
        cfg=json.loads((self.controller/'controller/controller.json').read_bytes())
        config={'origin':self.browser_origin,'code':grant['code'],'ca':str(self.controller/'dashboard/ca.crt'),
            'output':str(output),'controller':self.origin,'pin':self.pin,'cluster_id':cfg['cluster_id']}
        process=subprocess.Popen(['node',str(self.repo/'tests/browser/quick_join.cjs')],cwd=self.repo,env=self.env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        process.stdin.write(json.dumps(config));process.stdin.close()
        self.addCleanup(lambda:process.kill() if process.poll() is None else None)
        joined=False;deadline=time.monotonic()+100
        while process.poll() is None and time.monotonic()<deadline:
            signal=output/'pairing.json'
            if signal.exists() and not joined:
                pair=json.loads(signal.read_bytes())
                result=self.join(node,pair)
                self.assertEqual(result.returncode,0,'Actual node enrollment failed; private output suppressed')
                joined=True
            time.sleep(.1)
        if process.poll() is None:process.kill()
        process.wait(timeout=10)
        stdout,stderr=process.stdout.read(),process.stderr.read()
        process.stdout.close();process.stderr.close()
        self.assertEqual(process.returncode,0,'Synthetic Quick Join browser failed; private stderr suppressed')
        report=json.loads(stdout);self.assertTrue(report['passed']);self.assertTrue(joined)
        node_cfg=json.loads((node/'node/node.json').read_bytes())
        self.assertFalse((node/'node/storage.json').exists())
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes WHERE node_id=?',(node_cfg['node_id'],)).fetchone()[0],0)
        review=Path('/workspace/work/phase4/browser');review.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(output/'quick-join-mobile.png',review/'quick-join-mobile.png')


if __name__=='__main__':unittest.main()
