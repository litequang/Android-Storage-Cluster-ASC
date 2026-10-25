"""Exact baseline source validation and explicit platform/source-only boundaries."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
from unittest import mock

from asc.catalog.common import CatalogError, canonical
from asc.external.cli import host_guard
from asc.external.local import Tree
from asc.external.destination import LocalDirectory
from tests import test_external as fixture

BASELINE='acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c'
ROOT=Path(__file__).resolve().parents[1]


class ExternalCompatibilityTests(unittest.TestCase):
    setUp=fixture.ExternalBackupTests.setUp

    def test_exact_old_core_source_validates_new_capture_and_staged_metadata(self):
        adapter=LocalDirectory(self.dest)
        result=adapter.create(self.source,self.roots)
        self.assertEqual(adapter.verify(result['backup_id'],result['manifest_sha256'])['state'],'VERIFIED')
        recovery=self.base/'recovery';recovery.mkdir(mode=0o700)
        adapter.stage(result['backup_id'],result['manifest_sha256'],recovery,self.roots,self.source.doc['cluster_id'],100)
        old=self.base/'exact-baseline-source';old.mkdir(mode=0o700)
        archive=subprocess.check_output(['git','archive',BASELINE,'asc'],cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:tar.extractall(old,filter='data')
        code=("import json,sys; from asc.failover.state import validate,prepare_registry,export; "
              "from asc.catalog.common import canonical; "
              "raw=open(sys.argv[1],'rb').read(); doc=validate(json.loads(raw)); "
              "reg=prepare_registry(doc); rebuilt=export(reg.db,doc['revision'],doc['authority']); "
              "assert canonical(rebuilt)==raw; reg.db.close(); print('BASELINE_COMPATIBLE')")
        proc=subprocess.run([sys.executable,'-B','-c',code,str(recovery/'metadata.json')],cwd=old,
            capture_output=True,timeout=20)
        self.assertEqual(proc.returncode,0,'exact baseline must validate/roundtrip current captured schema without migration')
        self.assertEqual(proc.stdout.strip(),b'BASELINE_COMPATIBLE')
        self.assertEqual((recovery/'metadata.json').read_bytes(),canonical(self.source.doc))
        self.assertFalse((recovery/'registry.sqlite3').exists())

    def test_unqualified_platforms_fail_closed_without_state_access(self):
        with mock.patch('asc.external.cli.sys.platform','win32'),self.assertRaises(CatalogError):host_guard()
        with mock.patch('asc.external.cli.shutil.which',return_value='/synthetic/getprop'),self.assertRaises(CatalogError):host_guard()
        with mock.patch('asc.external.local.os.name','nt'),self.assertRaises(CatalogError):Tree(self.dest)
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()),['completed','store.json','working'])
