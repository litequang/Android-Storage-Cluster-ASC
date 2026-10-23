"""Owner-run POSIX installer checks in fake HOME; no phone/package/network access."""
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from asc.runtime import foreground_lock


@unittest.skipUnless(os.name == 'posix' and shutil.which('bash'), 'installer cases require Linux/Termux Bash')
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.repo = Path(__file__).resolve().parent.parent
        self.env = dict(os.environ, HOME=str(self.home), ASC_HOME=str(self.home / '.asc'),
                        PYTHONDONTWRITEBYTECODE='1', ASC_TEST_MODEL='ZTE V40',
                        PATH=str(self.bin) + os.pathsep + os.environ.get('PATH', ''))
        self._script('getprop', """#!/bin/sh
case "$1" in
  ro.product.model) printf '%s\\n' "$ASC_TEST_MODEL" ;;
  ro.product.manufacturer) printf 'ZTE\\n' ;;
  ro.build.version.sdk) printf '33\\n' ;;
  ro.build.version.release) printf '13\\n' ;;
esac
""")
        self._script('pkg', '#!/bin/sh\nprintf "unexpected package mutation\\n" >&2\nexit 99\n')
        self._script('python3', '#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' "$@"\n')
        self._script('openssl', '#!/bin/sh\nexit 99\n')  # Node already joined; must never execute.

    def _script(self, name, body):
        path = self.bin / name
        body = body.replace('#!/bin/sh', '#!' + shutil.which('sh'), 1)
        path.write_text(body, encoding='utf-8')
        path.chmod(0o700)

    def install(self, *args):
        return subprocess.run([shutil.which('bash'), str(self.repo / 'install.sh'), *args],
                              cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=45)

    def test_install_twice_preserves_identity_and_installed_source(self):
        private = self.home / '.asc'
        private.mkdir(mode=0o700)
        node = private / 'node.json'
        state = {'node_id': 'existing-node', 'cluster_id': 'test-cluster',
                 'controller': 'https://unused.invalid:8443', 'pin': 'A' * 64,
                 'token': secrets.token_urlsafe(32)}
        node.write_text(json.dumps(state), encoding='utf-8')
        original = node.read_bytes()
        first = self.install('node')
        self.assertEqual(first.returncode, 0, first.stderr)
        installed = self.home / 'asc-cluster' / 'asc' / 'probe.py'
        sentinel = installed.read_bytes() + b'\n# retained installed source\n'
        installed.write_bytes(sentinel)
        with foreground_lock(private, 'agent'):
            second = self.install('node')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(node.read_bytes(), original)
        self.assertEqual(installed.read_bytes(), sentinel)
        self.assertNotIn(state['token'], first.stdout + first.stderr + second.stdout + second.stderr)
        self.assertIn('no duplicate enrollment', second.stdout)

    def test_m51_and_unknown_identity_refused_before_source_or_identity_creation(self):
        for model in ('SM-M515F', '', 'unknown'):
            with self.subTest(model=model):
                self.env['ASC_TEST_MODEL'] = model
                result = self.install('controller')
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertFalse((self.home / 'asc-cluster').exists())
                self.assertFalse((self.home / '.asc').exists())

    def test_missing_dependency_only_reports_manual_action(self):
        # Limit PATH to controlled commands. No system openssl can satisfy the check.
        (self.bin / 'openssl').unlink()
        dirname = shutil.which('dirname')
        if dirname is None:
            self.skipTest('dirname required by installer')
        (self.bin / 'dirname').symlink_to(dirname)
        self.env['PATH'] = str(self.bin)
        result = self.install('node')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('Missing dependencies', result.stderr)
        self.assertIn('pkg install openssl', result.stderr)
        self.assertNotIn('unexpected package mutation', result.stderr)
        self.assertFalse((self.home / 'asc-cluster').exists())
        self.assertFalse((self.home / '.asc').exists())


if __name__ == '__main__':
    unittest.main()

