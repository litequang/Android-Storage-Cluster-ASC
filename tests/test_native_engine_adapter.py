"""Existing Engine JNI entrypoint exercised with actual private Linux I/O, no Android claim."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('android_native_engine',Path(__file__).parents[1]/'android/app/src/main/python/native_engine.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class NativeEngineAdapterTests(unittest.TestCase):
    def test_existing_engine_real_bytes_fsync_restart_and_no_network_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            proof=json.loads(adapter.self_test(str(Path(folder)/'new-private')))
            self.assertEqual(proof['state'],'LOCAL_ENGINE_SELF_TEST_PASS')
            self.assertTrue(proof['restart_sha_match']);self.assertFalse(proof['network_enrolled'])
            self.assertFalse(proof['node_runtime_supported']);self.assertFalse(proof['writer_authority'])
            self.assertTrue(proof['capabilities']['volumes'][0]['fsync_tested'])
    def test_existing_or_linked_roots_never_adopt_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);existing=root/'old';existing.mkdir();(existing/'keep').write_bytes(b'private-owned-fixture')
            link=root/'link';link.symlink_to(existing,target_is_directory=True)
            for path in (existing,link):
                with self.assertRaises((ValueError,FileExistsError)):adapter.self_test(str(path))
            self.assertEqual((existing/'keep').read_bytes(),b'private-owned-fixture')
            self.assertEqual(sorted(p.name for p in existing.iterdir()),['keep'])
    def test_library_info_is_not_node_authority(self):
        info=json.loads(adapter.info())
        self.assertEqual(info['implementation'],'asc.storage.engine')
        self.assertFalse(info['node_runtime_supported']);self.assertFalse(info['writer_authority'])

    def test_private_probe_identity_restart_quota_and_missing_manifest_refuse(self):
        import uuid
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'probe';app=str(uuid.uuid4())
            initial=json.loads(adapter.approve_probe(str(root),app,1048576,0))
            measured=json.loads(adapter.probe(str(root),app))['volume']
            self.assertTrue(measured['writable']);self.assertTrue(measured['fsync_tested'])
            self.assertEqual(initial,json.loads(adapter.approve_probe(str(root),app,1048576,0)))
            self.assertIsNone(json.loads(adapter.volume_status(str(root),app))['volume']['writable'])
            manifest=root/'manifest/manifest.sqlite3';manifest.rename(manifest.with_name('held.sqlite3'))
            self.assertEqual(json.loads(adapter.probe(str(root),app))['state'],'DEGRADED')
            self.assertFalse(manifest.exists())
            held=Path(folder)/'quota';adapter.approve_probe(str(held),app,1,0)
            self.assertEqual(json.loads(adapter.probe(str(held),app))['state'],'DEGRADED')
            self.assertEqual(list((held/'data/staging').iterdir()),[])
    def test_private_probe_future_format_holds_marker_and_schema(self):
        import uuid
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'probe';app=str(uuid.uuid4());adapter.approve_probe(str(root),app,1048576,0)
            marker=(root/'data/.asc-volume.json').read_bytes()
            path=root/'probe-approved.json';cfg=json.loads(path.read_bytes());cfg['format']=2;path.write_text(json.dumps(cfg))
            self.assertEqual(json.loads(adapter.probe(str(root),app))['state'],'DEGRADED')
            self.assertEqual((root/'data/.asc-volume.json').read_bytes(),marker)
            self.assertEqual(json.loads(path.read_bytes())['format'],2)
