"""Dependency diagnostics; real TLS/pin coverage stays in foundation/lifecycle suites."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from asc import identity


class CertificateDependencyTests(unittest.TestCase):
    def test_missing_openssl_is_actionable_and_creates_no_tls_files(self):
        with tempfile.TemporaryDirectory() as td:
            cert, key = Path(td) / 'cert.pem', Path(td) / 'key.pem'
            with mock.patch.object(identity.shutil, 'which', return_value=None), \
                    mock.patch.object(identity.subprocess, 'run') as run:
                with self.assertRaises(identity.DependencyError) as error:
                    identity.make_cert(cert, key)
            self.assertIn('PATH', str(error.exception))
            self.assertIn('openssl.exe', str(error.exception))
            run.assert_not_called()
            self.assertFalse(cert.exists())
            self.assertFalse(key.exists())

    def test_certificate_command_uses_resolved_executable_with_space_in_path(self):
        executable = str(Path('OpenSSL Development') / 'bin' / 'openssl.exe')
        with tempfile.TemporaryDirectory() as td:
            cert, key = Path(td) / 'cert.pem', Path(td) / 'key.pem'
            with mock.patch.object(identity.shutil, 'which', return_value=executable), \
                    mock.patch.object(identity.subprocess, 'run') as run, \
                    mock.patch.object(identity.os, 'chmod'):
                identity.make_cert(cert, key)
            argv = run.call_args.args[0]
            self.assertEqual(argv[0], executable)
            self.assertIn('rsa:2048', argv)
            self.assertIn('-sha256', argv)
            self.assertEqual(argv[argv.index('-keyout') + 1], str(key))
            self.assertTrue(run.call_args.kwargs['check'])
            self.assertNotIn('shell', run.call_args.kwargs)

    def test_executable_disappearing_after_lookup_remains_a_dependency_error(self):
        with mock.patch.object(identity.shutil, 'which', return_value='openssl.exe'), \
                mock.patch.object(identity.subprocess, 'run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(identity.DependencyError, 'could not start'):
                identity.make_cert('unused-cert.pem', 'unused-key.pem')

    def test_openssl_failure_does_not_reflect_subprocess_output(self):
        failure = subprocess.CalledProcessError(1, ['openssl'], stderr='private diagnostic marker')
        with mock.patch.object(identity.shutil, 'which', return_value='openssl.exe'), \
                mock.patch.object(identity.subprocess, 'run', side_effect=failure):
            with self.assertRaises(identity.DependencyError) as error:
                identity.make_cert('unused-cert.pem', 'unused-key.pem')
        self.assertNotIn('private diagnostic marker', str(error.exception))
