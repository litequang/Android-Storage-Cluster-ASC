"""Exact Dashboard archive and actual copyable documented extraction procedure."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from asc.demo import package


class DashboardPackageTests(unittest.TestCase):
    def test_exact_archive_guided_extraction_manifest_source_and_no_private_payload(self):
        repo=Path(__file__).resolve().parents[1];archive=repo/'candidates/asc-controller-0.5.0-dashboard-alpha.tar.gz'
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),archive.with_name(archive.name+'.sha256').read_text().split()[0])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/'documented-extraction'
            with tarfile.open(archive) as saved:
                guide=saved.extractfile('asc-demo-alpha/docs/DASHBOARD-INSTALL.md').read().decode()
                script=guide.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
                for member in saved.getmembers():
                    self.assertTrue(member.isfile());self.assertTrue(member.name.startswith('asc-demo-alpha/'))
                    raw=saved.extractfile(member).read()
                    self.assertIsNone(re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/=]{16,}',raw),member.name)
            run=subprocess.run([sys.executable,'-I','-B','-',str(archive),str(target)],input=script,text=True,capture_output=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            source=target/'asc-demo-alpha';manifest=package.verify(source)
            self.assertEqual(manifest['version'],'0.5.0-dashboard-alpha')
            for guide_name in ('DASHBOARD-INSTALL.md','DASHBOARD-OPERATIONS.md','PHASE4-WEB-APP.md','ANDROID-NATIVE-PILOT.md'):
                self.assertIn('docs/'+guide_name,manifest['files'])
            current={p.relative_to(repo).as_posix():p.read_bytes() for p in (repo/'asc').rglob('*.py')}
            self.assertEqual({p for p in manifest['files'] if p.startswith('asc/') and p.endswith('.py')},set(current))
            for name,raw in current.items():self.assertTrue((source/name).read_bytes()==raw,name)
            rebuilt=root/'independent-source.tar.gz';package.build(repo,rebuilt)
            self.assertTrue(archive.read_bytes()==rebuilt.read_bytes(),'Archive not exact current package inputs')
        for name,expected in (
            ('candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz','6a60bd4180bc338d8c62eff4ef1347082a0e6c0ce36e06143ff53baa791b9d57'),
            ('candidates/asc-linux-access-0.1.0-internal.tar.gz','d6f751d7bd93f3f438bec1c983b05b133b209870fe164cf7ea4bcf9e268e10d9'),
            ('android-artifacts/asc-native-node-0.4.1-internal-debug.apk','aec65c2ca5541aab4060e19616204eef8caf4d2f0d6e7a3e27010dd819cf60f5')):
            self.assertEqual(hashlib.sha256((repo/name).read_bytes()).hexdigest(),expected)


if __name__=='__main__':unittest.main()
