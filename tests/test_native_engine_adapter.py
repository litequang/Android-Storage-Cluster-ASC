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
