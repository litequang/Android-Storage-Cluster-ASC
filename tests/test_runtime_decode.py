"""Immutable schema validation reuse must never cache runtime write authority."""
import base64
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

from asc.catalog.common import CatalogError, canonical, uid
from asc.failover import state
from asc.failover.runtime import Runtime


class RuntimeDecodeTests(unittest.TestCase):
    def setUp(self):
        state._validated_runtime_bytes.cache_clear()
        self.addCleanup(state._validated_runtime_bytes.cache_clear)
        reg = state.MemoryRegistry(uid())
        with closing(reg.db) as db:
            reg.seed_self('Decode test Controller', {'protected': False})
            self.doc = state.export(db, 1, {'node_id': 'voter-a', 'term': 3})
        self.raw = canonical(self.doc)

    def runtime(self):
        tmp = tempfile.TemporaryDirectory(prefix='asc-runtime-validation-')
        self.addCleanup(tmp.cleanup)
        runtime = object.__new__(Runtime)
        runtime.path = Path(tmp.name)/'runtime.sqlite3'
        runtime.lock = threading.RLock()
        runtime.local = threading.local()
        runtime.node_id = 'voter-a'
        runtime.cluster, runtime.epoch = self.doc['cluster_id'], self.doc['epoch']
        runtime.mode, runtime.term = 'Leader', 3
        runtime.fatal, runtime.cache_schema = False, None
        result = {'state': {'index': 1, 'term': 3, 'cluster_id': runtime.cluster,
                  'epoch': runtime.epoch, 'receipts': {},
                  'document': base64.b64encode(self.raw).decode(),
                  'document_sha256': hashlib.sha256(self.raw).hexdigest()}}
        runtime.client = SimpleNamespace(state=mock.Mock(return_value=result),
            status=mock.Mock(return_value={'role': 'Leader', 'term': 3, 'quarantined': False}))
        return runtime, result

    def test_repeated_bytes_validate_once_but_return_independent_nested_documents(self):
        with mock.patch.object(state, 'validate', wraps=state.validate) as validate:
            first = state.decode_validated(self.raw)
            second = state.decode_validated(self.raw)
            self.assertEqual(validate.call_count, 1)
        first['authority']['term'] = 100
        first['catalog']['files'].append({'untrusted': True})
        second['tables']['nodes'].append({'untrusted': True})
        self.assertEqual(state.decode_validated(self.raw), self.doc)

    def test_tampered_columns_and_future_schema_never_reuse_valid_result(self):
        state.decode_validated(self.raw)
        for change in ('private-column', 'schema', 'epoch'):
            bad = copy.deepcopy(self.doc)
            if change == 'private-column':
                bad['tables']['nodes'][0]['private_key'] = 'forbidden'
            elif change == 'schema':
                bad['schema'] = 999
            else:
                bad['epoch'] = uid()
            with self.subTest(change=change), self.assertRaises(CatalogError):
                state.decode_validated(canonical(bad))
        self.assertEqual(state.decode_validated(self.raw), self.doc)

    def test_invalid_and_oversized_inputs_are_not_retained(self):
        for raw in (b'{', b'\xff', b'null', b'['*2000+b']'*2000,
                    b' '* (2*1024**2+1), bytearray(self.raw)):
            with self.subTest(kind=type(raw).__name__, size=len(raw)):
                with self.assertRaises(CatalogError):
                    state.decode_validated(raw)
        self.assertEqual(state._validated_runtime_bytes.cache_info().currsize, 0)

    def test_successful_cache_is_bounded_and_does_not_hide_changed_revision(self):
        for revision in (1, 2, 3):
            doc = {**self.doc, 'revision': revision}
            self.assertEqual(state.decode_validated(canonical(doc)), doc)
        self.assertEqual(state._validated_runtime_bytes.cache_info().currsize, 2)

    def test_warm_validation_never_converts_quorum_loss_into_strong_view_or_writer(self):
        runtime, _ = self.runtime()
        self.assertFalse(runtime.view(strong=True)['stale'])
        runtime.client.state.side_effect = CatalogError('quorum_read_unavailable', 503)
        with self.assertRaises(CatalogError):
            runtime.view(strong=True)
        with self.assertRaises(CatalogError):
            runtime.ensure_ready()
        stale = runtime.view()
        self.assertTrue(stale['stale'])
        self.assertTrue(stale['read_only'])
        self.assertIsNone(runtime.term)

    def test_warm_validation_still_checks_envelope_identity_hash_and_index(self):
        runtime, result = self.runtime()
        runtime.view(strong=True)
        for change in ('cluster', 'epoch', 'hash', 'index', 'term'):
            bad = copy.deepcopy(result)
            if change in ('cluster', 'epoch'):
                bad['state']['cluster_id' if change == 'cluster' else 'epoch'] = uid()
            elif change == 'hash':
                bad['state']['document_sha256'] = 'f'*64
            else:
                bad['state'][change] = 0
            runtime.client.state.return_value = bad
            with self.subTest(change=change), self.assertRaises(CatalogError):
                runtime.view(strong=True)

    def test_noncanonical_wire_bytes_still_fail_even_when_document_was_validated(self):
        runtime, result = self.runtime()
        runtime.view(strong=True)
        raw = json.dumps(self.doc, indent=1).encode()
        result['state'].update(document=base64.b64encode(raw).decode(),
                               document_sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaises(CatalogError):
            runtime.view(strong=True)

    def test_warm_validation_cannot_hide_corrupted_durable_cache(self):
        runtime, _ = self.runtime()
        runtime.view(strong=True)
        with closing(sqlite3.connect(runtime.path)) as db, db:
            db.execute("UPDATE projection SET sha256=?", ('f'*64,))
        with self.assertRaises(CatalogError) as rejected:
            runtime.view(strong=True)
        self.assertEqual(rejected.exception.code, 'runtime_cache_quarantined')
        self.assertTrue(runtime.fatal)
