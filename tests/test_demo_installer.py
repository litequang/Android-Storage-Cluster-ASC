"""Actual package/installer execution in isolated fake Android HOME; no phone access."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from asc.demo.package import build, verify


class DemoInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.repo = Path(__file__).resolve().parents[1]
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1',
                        ASC_TEST_MODEL='ZTE V40', PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        self.script('getprop', '''case "$1" in
ro.product.model) printf '%s\\n' "$ASC_TEST_MODEL";;
ro.product.manufacturer) echo ZTE;;
ro.build.version.sdk) echo 33;;
esac
''')
        self.script('pkg', 'echo forbidden-package-mutation >&2; exit 99\n')
        self.script('python3', 'exec ' + shlex.quote(sys.executable) + ' "$@"\n')
        self.archive = self.root / 'demo.tar.gz'
        self.report = build(self.repo, self.archive)
        with tarfile.open(self.archive) as archive:
            for entry in archive.getmembers():
                self.assertTrue(entry.isfile())
                self.assertFalse(entry.name.startswith('/') or '..' in Path(entry.name).parts)
            archive.extractall(self.root / 'unpacked', filter='data')
        self.source = self.root / 'unpacked/asc-demo-alpha'
        self.prefix = self.home / 'demo-code'

    def script(self, name, body):
        path = self.bin / name
        path.write_text('#!' + shutil.which('sh') + '\n' + body)
        path.chmod(0o700)

    def run_cli(self, *args, installed=False):
        script = self.prefix / 'bin/asc-demo' if installed else self.source / 'scripts/demo-alpha.sh'
        return subprocess.run([shutil.which('sh'), str(script), *args], env=self.env,
                              capture_output=True, text=True, timeout=30, cwd=self.root)

    def test_package_deterministic_inventory_checksums_and_tamper_refusal(self):
        other = self.root / 'same.tar.gz'
        build(self.repo, other)
        self.assertEqual(self.archive.read_bytes(), other.read_bytes())
        self.assertEqual(self.report['sha256'], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertEqual(verify(self.source)['release_id'], self.report['release_id'])
        (self.source / 'asc/probe.py').write_text('# tampered\n')
        result = self.run_cli('install', '--prefix', str(self.prefix))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.prefix.exists())

    def test_preflight_dry_run_rerun_preserves_source_and_separate_private_state(self):
        preflight = self.run_cli('preflight')
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        self.assertFalse(json.loads(preflight.stdout)['write_tested'])
        dry = self.run_cli('install', '--prefix', str(self.prefix), '--dry-run')
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertFalse(self.prefix.exists())
        state = self.home / '.asc-demo'
        state.mkdir(mode=0o700)
        identity = state / 'identity-sentinel'
        identity.write_bytes(os.urandom(128))
        before = identity.read_bytes()
        first = self.run_cli('install', '--prefix', str(self.prefix))
        self.assertEqual(first.returncode, 0, first.stderr)
        installed = self.prefix / 'releases' / self.report['release_id']
        snapshot = {p.relative_to(installed): p.read_bytes() for p in installed.rglob('*') if p.is_file()}
        again = self.run_cli('install', '--prefix', str(self.prefix))
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(snapshot, {p.relative_to(installed): p.read_bytes() for p in installed.rglob('*') if p.is_file()})
        self.assertEqual(identity.read_bytes(), before)
        self.assertEqual(self.run_cli('preflight', installed=True).returncode, 0)
        (installed / 'asc/probe.py').write_text('# changed')
        self.assertNotEqual(self.run_cli('install', '--prefix', str(self.prefix)).returncode, 0)
        self.assertEqual(identity.read_bytes(), before)

    def test_protected_unknown_missing_dependency_and_unmarked_paths_fail_closed(self):
        for model in ('SM-M515F', '', 'unknown'):
            with self.subTest(model=model):
                self.env['ASC_TEST_MODEL'] = model
                result = self.run_cli('install', '--prefix', str(self.prefix))
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.prefix.exists())
                self.assertNotIn('forbidden-package-mutation', result.stdout + result.stderr)
        self.env['ASC_TEST_MODEL'] = 'ZTE V40'
        self.script('openssl', 'exit 99\n')
        self.assertNotEqual(self.run_cli('install', '--prefix', str(self.prefix)).returncode, 0)
        self.assertFalse(self.prefix.exists())
        (self.bin / 'openssl').unlink()
        self.prefix.mkdir()
        sentinel = self.prefix / 'old-source'
        sentinel.write_text('keep')
        self.assertNotEqual(self.run_cli('install', '--prefix', str(self.prefix)).returncode, 0)
        self.assertEqual(sentinel.read_text(), 'keep')
        link = self.home / 'linked'
        link.symlink_to(self.root)
        self.assertNotEqual(self.run_cli('install', '--prefix', str(link / 'escape')).returncode, 0)
        self.assertFalse((self.root / 'escape').exists())
        traversal = self.home / 'unused' / '..' / 'escape-two'
        self.assertNotEqual(self.run_cli('install', '--prefix', str(traversal)).returncode, 0)
        self.assertFalse((self.home / 'escape-two').exists())


if __name__ == '__main__':
    unittest.main()
