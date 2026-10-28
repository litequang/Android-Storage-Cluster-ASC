"""Published baseline selection must never silently exercise the current APK."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.qualify_native_catalog import PUBLISHED_APKS, selected_apk


ROOT=Path(__file__).resolve().parents[1]


class QualificationArtifactTests(unittest.TestCase):
    def test_exact_published_apks_are_distinct_preserved_inputs(self):
        paths=[]
        for artifact,(name,sha) in PUBLISHED_APKS.items():
            target=selected_apk(ROOT,artifact)
            self.assertEqual(target,ROOT/'android-artifacts'/name)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),sha)
            paths.append(target)
        self.assertEqual(len(set(paths)),2)
        self.assertNotEqual(PUBLISHED_APKS['published4'][1],PUBLISHED_APKS['published5'][1])

    def test_missing_or_corrupt_published_baseline_never_falls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            current=root/'android/app/build/outputs/apk/debug/app-debug.apk'
            current.parent.mkdir(parents=True);current.write_bytes(b'newer build exists')
            for artifact,(name,_) in PUBLISHED_APKS.items():
                with self.subTest(artifact=artifact,state='missing'):
                    with self.assertRaises(ValueError):selected_apk(root,artifact)
                old=root/'android-artifacts'/name;old.parent.mkdir(exist_ok=True)
                old.write_bytes(b'corrupted published baseline')
                with self.subTest(artifact=artifact,state='corrupt'):
                    with self.assertRaises(ValueError):selected_apk(root,artifact)
                self.assertEqual(current.read_bytes(),b'newer build exists')
                self.assertEqual(old.read_bytes(),b'corrupted published baseline')

    def test_unlisted_paths_and_artifacts_refuse(self):
        for artifact in ('../published4','/tmp/arbitrary.apk','published6',''):
            with self.subTest(artifact=artifact):
                with self.assertRaises(ValueError):selected_apk(ROOT,artifact)
