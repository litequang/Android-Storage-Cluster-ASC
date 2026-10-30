"""Exact immutable published Linux Access0.1.0 -> current Controller/browser."""
import json
import os
from pathlib import Path
import ssl
import subprocess
import tempfile
import types
import unittest

from asc.identity import fingerprint_from_pem
from tests import test_access_browser as browser_fixture
from tests import test_demo_dashboard as backend_fixture
from tools import package_access


class LegacyAccessBrowserTests(unittest.TestCase):
    def setUp(self):
        backend=backend_fixture.DashboardAPITests();self.addCleanup(backend.doCleanups);backend.setUp()
        temporary=tempfile.TemporaryDirectory(prefix='.asc-old-access-',dir=Path.home());self.addCleanup(temporary.cleanup)
        base=Path(temporary.name);code=base/'code';env=base/'env';root=base/'gateway'
        package_access.unpack(backend.repo/'candidates/asc-linux-access-0.1.0-internal.tar.gz',code,
                              'd6f751d7bd93f3f438bec1c983b05b133b209870fe164cf7ea4bcf9e268e10d9')
        package_access.prepare_env(code,env)
        origin='https://127.0.0.1:'+str(backend.free_port())
        config=dict(format=1,mode='private-gateway',frontend_origin=origin,upstream_origin=backend.browser_origin,
            upstream_pin=fingerprint_from_pem(backend.controller/'dashboard/server.crt').lower(),
            upstream_mode='single-writer-demo',max_body_bytes=1024**2)
        profile=base/'profile.json';profile.write_text(json.dumps(config));profile.chmod(0o600)
        cli=[str(env/'bin/python'),'-I','-B',str(code/'access.py'),'gateway','--root',str(root)]
        setup=subprocess.run(cli+['init','--profile',str(profile)],env=os.environ.copy(),capture_output=True,text=True,timeout=45)
        self.assertEqual(setup.returncode,0,'Exact old bundle failed to init; private output suppressed')
        log=(base/'gateway.log').open('w+');self.addCleanup(log.close)
        process=subprocess.Popen(cli+['serve'],env=os.environ.copy(),stdout=log,stderr=log,text=True)
        def stop():
            if process.poll() is None:process.terminate();process.wait(timeout=20)
        self.addCleanup(stop)
        import http.client
        context=ssl.create_default_context(cafile=str(root/'dashboard/ca.crt'))
        def ready():
            self.assertIsNone(process.poll(),'Exact old gateway exited; private output suppressed')
            c=http.client.HTTPSConnection('127.0.0.1',int(origin.rsplit(':',1)[1]),context=context,timeout=1)
            try:c.connect();return True
            finally:c.close()
        backend.wait_for(ready)
        self.f=types.SimpleNamespace(f=backend,temp=temporary,root=root,origin=origin,
            artifact_directory='/workspace/work/dashboard-browser/legacy-access')

    def test_exact_published_010_file_gateway_keeps_browser_login_files_and_fallback(self):
        # ORIGINAL existing trusted/untrusted TLS/PWA/login/upload/replica/SHA/
        # actual stop/fallback/offline assertions, not mocked success or new limits.
        browser_fixture.PrivateGatewayBrowserTests.test_actual_chromium_owner_files_pwa_sha_fallback_and_network_loss(self)


if __name__=='__main__':unittest.main()
