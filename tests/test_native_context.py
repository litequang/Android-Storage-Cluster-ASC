"""Explicit context safety/real private filesystem; NOT Android Keystore evidence."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from asc.catalog.common import canonical
from asc.node.context import ContextLocked, NodeContext, android_device, decode


def synthetic_build():
    return {'manufacturer': 'Google', 'model': 'sdk_gphone64_x86_64', 'device': 'emu64xa',
            'product': 'sdk_gphone64_x86_64', 'hardware': 'ranchu',
            'fingerprint': 'google/sdk_gphone64_x86_64/generic:15/test', 'sdk': 35, 'debug': True}


class MemoryCredentials:
    """Test-only CAS fake. No encryption/Android/security claim from this provider."""
    def __init__(self):
        self.raw = None
        self.loads = 0
        self.failure = False

    def load(self):
        self.loads += 1
        if self.failure:
            raise ValueError('synthetic lost/corrupt key')
        return self.raw

    def compare_exchange(self, expected, replacement):
        if self.failure or self.raw != expected:
            raise ValueError('synthetic publication failure/conflict')
        self.raw = replacement


class NativeContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.provider = MemoryCredentials()
        self.app = str(uuid.uuid4())

    def context(self, build=None, app=None):
        return NodeContext(self.parent, self.provider, app or self.app, build or synthetic_build())

    def test_explicit_initialize_restart_no_global_home_or_cli_dependencies(self):
        from asc.identity import HOME
        before = dict(os.environ)
        with patch('subprocess.run', side_effect=AssertionError('no subprocess')), \
                patch('getpass.getpass', side_effect=AssertionError('no interactive input')):
            initial = self.context().initialize()
            record = self.provider.raw
            anchor = (self.parent / 'native-node-v1/context.json').read_bytes()
            self.assertEqual(self.context().public_status(), initial)
            self.assertEqual(self.context().initialize(), initial)
            with self.context().operation():
                self.assertEqual(self.context().public_status(), initial)
            self.assertEqual(record, self.provider.raw)
            self.assertEqual(anchor, (self.parent / 'native-node-v1/context.json').read_bytes())
        self.assertEqual(before, dict(os.environ))
        from asc.identity import HOME as after_home
        self.assertEqual(HOME, after_home)
        self.assertIsNone(initial['node_id'])
        self.assertIsNone(initial['cluster_id'])
        self.assertFalse(initial['runtime_start_supported'])
        self.assertFalse(initial['writer_authority'])
        self.assertEqual(initial['device_scope'], 'LINUX_HOSTED_ANDROID_SYNTHETIC')
        self.assertEqual(initial['tls'], 'NOT_CONFIGURED')

    def test_status_and_constructor_cannot_initialize(self):
        context = self.context()
        with self.assertRaises(ContextLocked):
            context.public_status()
        self.assertIsNone(self.provider.raw)
        self.assertEqual(list(self.parent.iterdir()), [])

    def test_missing_credential_or_key_never_reinitializes_existing_root(self):
        self.context().initialize()
        anchor = self.parent / 'native-node-v1/context.json'
        original = anchor.read_bytes()
        for raw, failure in ((None, False), ('{}', False), (self.provider.raw, True)):
            self.provider.raw, self.provider.failure = raw, failure
            for operation in ('initialize', 'public_status'):
                with self.assertRaises(ContextLocked):
                    getattr(self.context(), operation)()
            self.assertEqual(original, anchor.read_bytes())

    def test_missing_root_or_anchor_is_not_recreated(self):
        initial = self.context().initialize()
        root = self.parent / 'native-node-v1'
        anchor = root / 'context.json'
        anchor.rename(root / 'held-anchor.json')
        with self.assertRaises(ContextLocked):
            self.context().initialize()
        self.assertFalse(anchor.exists())
        (root / 'held-anchor.json').rename(anchor)
        root.rename(self.parent / 'held-root')
        with self.assertRaises(ContextLocked):
            self.context().initialize()
        self.assertFalse(root.exists())
        self.assertEqual(initial['context_id'], json.loads(self.provider.raw)['context_id'])

    def test_root_replacement_symlinks_hardlinks_and_marker_mismatch_hold(self):
        self.context().initialize()
        root = self.parent / 'native-node-v1'
        anchor = root / 'context.json'
        original = anchor.read_bytes()
        held = self.parent / 'held'
        root.rename(held)
        root.mkdir(mode=0o700)
        (root / 'context.json').write_bytes(original)
        with self.assertRaises(ContextLocked):
            self.context().public_status()
        (root / 'context.json').unlink(); root.rmdir()
        root.symlink_to(held, target_is_directory=True)
        with self.assertRaises(ContextLocked):
            self.context().public_status()
        root.unlink(); held.rename(root)
        anchor.rename(root / 'held.json')
        anchor.symlink_to(root / 'held.json')
        with self.assertRaises(ContextLocked):
            self.context().public_status()
        anchor.unlink(); os.link(root / 'held.json', anchor)
        with self.assertRaises(ContextLocked):
            self.context().public_status()
        anchor.unlink(); (root / 'held.json').rename(anchor)
        anchor.write_text(json.dumps(dict(json.loads(original), app_id=str(uuid.uuid4()))))
        with self.assertRaises(ContextLocked):
            self.context().initialize()
        self.assertEqual(json.loads(original)['app_id'], json.loads(self.provider.raw)['app_id'])

    def test_unknown_future_duplicate_and_type_alias_records_refuse(self):
        self.context().initialize()
        saved = self.provider.raw
        for change in ({'format': 2}, {'format': True}, {'revision': False}, {'revision': -1},
                       {'unexpected': 1}, {'pending': {}}, {'node': {}}, {'tls': {}}, {'storage': {}}):
            self.provider.raw = canonical(dict(json.loads(saved), **change)).decode()
            with self.assertRaises(ContextLocked):
                self.context().load()
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '[' * 10000, 'x' * 65537):
            with self.assertRaises(ContextLocked):
                decode(raw)

    def test_protected_unknown_and_changed_device_refuse_before_credentials(self):
        for field in ('manufacturer', 'model', 'device', 'product'):
            build = synthetic_build(); build[field] = 'SM-M515F'
            with self.assertRaises(ContextLocked):
                self.context(build)
        for changes in ({'model': 'unknown', 'debug': False}, {'manufacturer': 'unknown', 'debug': False}, {'debug': False},
                        {'sdk': 25}, {'sdk': True}, {'product': 'unknown'}):
            build = dict(synthetic_build(), **changes)
            with self.assertRaises(ContextLocked):
                self.context(build)
        self.assertEqual(self.provider.loads, 0)
        # Official AOSP image may have manufacturer=unknown. Only the separately
        # identified DEBUG SDK/ranchu/fingerprint fixture scope accepts it, never
        # an unknown phone or a model-only override.
        aosp = dict(synthetic_build(), manufacturer='unknown')
        self.assertEqual(android_device(aosp)['scope'], 'LINUX_HOSTED_ANDROID_SYNTHETIC')
        self.context().initialize()
        with self.assertRaises(ContextLocked):
            self.context(dict(synthetic_build(), model='sdk_changed')).load()
        # A compatible OS update need not reset identity.
        self.assertEqual(self.context(dict(synthetic_build(), sdk=36,
                         fingerprint='google/sdk/upgrade')).public_status()['state'], 'CONTEXT_READY')

    def test_partial_publication_failure_keeps_root_for_review(self):
        class FailOnPublish(MemoryCredentials):
            def compare_exchange(self, expected, replacement):
                raise OSError('injected publication loss')
        self.provider = FailOnPublish()
        with self.assertRaises(ContextLocked):
            self.context().initialize()
        anchor = self.parent / 'native-node-v1/context.json'
        original = anchor.read_bytes()
        with self.assertRaises(ContextLocked):
            self.context().initialize()
        self.assertIsNone(self.provider.raw)
        self.assertEqual(anchor.read_bytes(), original)

    def test_recovery_or_legacy_state_is_never_adopted(self):
        for marker in ('RECOVERY_READ_ONLY.json', 'READY.json'):
            path = self.parent / marker; path.write_text('{}')
            with self.assertRaises(ContextLocked):
                self.context().initialize()
            self.assertIsNone(self.provider.raw)
            path.unlink()
        self.context().initialize()
        for name in ('node.json', 'controller.json', 'registry.sqlite3', 'runtime.sqlite3',
                     'storage.json', 'enrollment_pending.json'):
            path = self.parent / 'native-node-v1' / name
            path.write_text('synthetic preserved legacy state')
            with self.assertRaises(ContextLocked):
                self.context().initialize()
            self.assertEqual(path.read_text(), 'synthetic preserved legacy state')
            path.unlink()

    def test_provider_cas_conflict_and_app_binding(self):
        self.context().initialize()
        old = self.provider.raw
        with self.assertRaises(ValueError):
            self.provider.compare_exchange(None, old)
        with self.assertRaises(ContextLocked):
            self.context(app=str(uuid.uuid4())).load()
        self.assertEqual(self.provider.raw, old)
