"""Exact-byte structural reuse must never cache authority or mutable input."""
import copy
import unittest
from unittest import mock

from asc.catalog.common import CatalogError, digest
from asc.failover import state
from tests import test_replication as fixture


class RuntimeValidationTests(unittest.TestCase):
    def setUp(self):
        holder=fixture.DynamicPolicyTests();holder.setUp();self.addCleanup(holder.doCleanups)
        self.doc=copy.deepcopy(holder.runtime.doc)
        state._validated_catalog_bytes.cache_clear()

    def test_exact_catalog_bytes_reuse_only_structural_validation(self):
        with mock.patch.object(state,'catalog_validate',wraps=state.catalog_validate) as validator:
            state.validate(self.doc);state.validate(copy.deepcopy(self.doc))
            self.assertEqual(validator.call_count,1)
            # Replicated runtime identity/extension checks still run on every call.
            changed=copy.deepcopy(self.doc);changed['authority']['term']=0
            with self.assertRaises(CatalogError):state.validate(changed)
            changed=copy.deepcopy(self.doc);changed['cluster_id']='different-cluster'
            with self.assertRaises(CatalogError):state.validate(changed)

    def test_mutated_history_digest_and_materialization_cannot_reuse_old_validation(self):
        state.validate(self.doc)
        for rehash in (False,True):
            changed=copy.deepcopy(self.doc)
            event=changed['catalog']['events'][-1]
            event['payload']['file']['size']+=1
            if rehash:
                event['digest']=digest({k:v for k,v in event.items() if k!='digest'})
                changed['catalog']['head_digest']=event['digest']
            with self.subTest(rehash=rehash),self.assertRaises(CatalogError):state.validate(changed)
        state.validate(self.doc)

    def test_python_type_aliases_and_failed_validation_never_enter_cache(self):
        state.validate(self.doc)
        for field in ('events','files','replicas'):
            changed=copy.deepcopy(self.doc);changed['catalog'][field]=tuple(changed['catalog'][field])
            with self.subTest(field=field),self.assertRaises(CatalogError):state.validate(changed)
        before=state._validated_catalog_bytes.cache_info().currsize
        changed=copy.deepcopy(self.doc);changed['catalog']['schema']=999
        for _ in range(2):
            with self.assertRaises(CatalogError):state.validate(changed)
        self.assertEqual(state._validated_catalog_bytes.cache_info().currsize,before)
        self.assertEqual(state._validated_catalog_bytes.cache_info().maxsize,2)
