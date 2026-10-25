"""Anchored offline verification, UNKNOWN semantics and locked retention."""
import copy
import io
import json
import os
from pathlib import Path
import unittest
from unittest import mock
from contextlib import redirect_stdout

from asc.catalog.common import canonical, digest, uid
from asc.external.cli import main
from asc.external.engine import complete_receipt
from asc.external.verify import verify, inventory, retention_preview
from tests import test_external as fixture


class ExternalVerificationTests(unittest.TestCase):
    # Reuse fixture setup only; do not inherit/discover duplicate old test cases.
    setUp=fixture.ExternalBackupTests.setUp

    def completed(self):
        result=self.engine.create(self.source,self.roots)
        folder=self.dest/'completed'/result['backup_id']
        return result,folder

    def test_valid_anchor_timebound_full_coverage_and_known_newer_checkpoint(self):
        result,folder=self.completed()
        report=verify(self.store,result['backup_id'],result['manifest_sha256'],100,self.source.doc['cluster_id'])
        self.assertEqual(report['state'],'VERIFIED');self.assertEqual(report['objects'],2)
        self.assertTrue(report['integrity_verified']);self.assertIsInstance(report['verified_at'],int)
        self.assertFalse(report['writer_recovery_supported']);self.assertFalse(report['latest_history_proven'])
        stale=verify(self.store,result['backup_id'],result['manifest_sha256'],101)
        self.assertEqual(stale['state'],'STALE');self.assertTrue(stale['integrity_verified'])
        self.assertEqual(inventory(self.store)['backups'][0]['state'],'COMPLETE_UNVERIFIED')

    def test_wrong_anchor_tampered_manifest_even_rehashed_receipt_and_metadata_mismatch(self):
        result,folder=self.completed();manifest=json.loads((folder/'manifest.json').read_bytes())
        self.assertEqual(verify(self.store,result['backup_id'],'0'*64)['state'],'CORRUPT')
        manifest['created_at']+=1
        (folder/'manifest.json').write_bytes(canonical(manifest))
        (folder/'complete.json').write_bytes(canonical(complete_receipt(manifest)))
        self.assertEqual(verify(self.store,result['backup_id'],result['manifest_sha256'])['state'],'CORRUPT')
        (folder/'metadata.json').write_bytes(canonical({}))
        self.assertEqual(verify(self.store,result['backup_id'],digest(manifest))['state'],'CORRUPT')

    def test_missing_and_corrupt_bytes_and_extra_object_are_never_verified(self):
        result,folder=self.completed();body=next((folder/'objects').iterdir());data=body.read_bytes()
        body.write_bytes(b'corrupt')
        self.assertEqual(verify(self.store,result['backup_id'],result['manifest_sha256'])['state'],'CORRUPT')
        body.write_bytes(data);body.unlink()
        self.assertEqual(verify(self.store,result['backup_id'],result['manifest_sha256'])['state'],'CORRUPT')
        body.write_bytes(data);body.chmod(0o600)
        extra=folder/'objects'/'unknown.blob';extra.write_bytes(b'extra')
        self.assertEqual(verify(self.store,result['backup_id'],result['manifest_sha256'])['state'],'CORRUPT')

    def test_permission_io_and_unavailable_store_stay_unknown_not_zero(self):
        result,folder=self.completed();body=next((folder/'objects').iterdir());body.chmod(0)
        try:
            self.assertEqual(verify(self.store,result['backup_id'],result['manifest_sha256'])['state'],'UNKNOWN')
        finally:body.chmod(0o600)
        with mock.patch.object(self.store,'open',side_effect=PermissionError):
            self.assertEqual(inventory(self.store)['count'],None)
            self.assertEqual(verify(self.store,result['backup_id'],result['manifest_sha256'])['state'],'UNKNOWN')
            self.assertIsNone(retention_preview(self.store)['holds'])

    def test_incomplete_inventory_and_last_backup_retention_never_delete(self):
        result,folder=self.completed();before={p:p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        held=retention_preview(self.store)
        self.assertFalse(held['deletion_supported']);self.assertEqual(held['candidates'],[])
        self.assertEqual(held['physical_deletions'],0);self.assertEqual(len(held['holds']),1)
        self.assertEqual(before,{p:p.read_bytes() for p in folder.rglob('*') if p.is_file()})
        self.source.fail_read=True
        with self.assertRaises(OSError):self.engine.create(self.source,self.roots)
        backup_id=next((self.dest/'working').iterdir()).name
        self.assertEqual(verify(self.store,backup_id,'0'*64)['state'],'INCOMPLETE')
        self.assertEqual(len(retention_preview(self.store)['holds']),2)

    def test_cli_lists_verifies_and_rejects_android_without_printing_secrets(self):
        result,folder=self.completed();out=io.StringIO()
        with redirect_stdout(out):
            code=main(['verify','--store',str(self.dest),'--backup-id',result['backup_id'],'--expected-sha256',result['manifest_sha256']])
        self.assertEqual(code,0);self.assertEqual(json.loads(out.getvalue())['state'],'VERIFIED')
        for env in ({'PREFIX':'/data/data/com.termux/files/usr'},{'ANDROID_ROOT':'/system'}):
            out=io.StringIO()
            with mock.patch.dict(os.environ,env),redirect_stdout(out):
                code=main(['list','--store',str(self.dest)])
            self.assertEqual(code,1);self.assertEqual(json.loads(out.getvalue())['state'],'FAILED')
            self.assertNotIn(str(self.dest),out.getvalue())
