"""Actual private operator-document I/O, interrupted flush and namespace swap."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from asc.bridge.contract import Refused
from asc.demo.dashboard import document
from asc.storage.errors import StorageError


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.asc-history-doc-',dir=Path.home());self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.parent=self.root/'private';self.parent.mkdir(mode=0o700)
        self.path=self.parent/'history.json';document.write(self.path,{'format':1,'proof':'old'})

    def test_failed_fsync_preserves_original_and_cleans_only_own_temporary(self):
        unrelated=self.parent/'.history-owner-file';unrelated.write_bytes(b'preserve unrelated file')
        before=self.path.read_bytes()
        with mock.patch.object(document.os,'fsync',side_effect=OSError('synthetic flush failure')):
            with self.assertRaises(OSError):document.write(self.path,{'format':1,'proof':'new'})
        self.assertEqual(self.path.read_bytes(),before);self.assertEqual(unrelated.read_bytes(),b'preserve unrelated file')
        self.assertEqual({p.name for p in self.parent.iterdir()},{'history.json',unrelated.name})

    def test_swapped_parent_cannot_redirect_write_outside_approved_directory(self):
        outside=self.root/'outside';outside.mkdir(mode=0o700);protected=outside/'history.json';protected.write_bytes(b'outside user bytes')
        held=self.root/'held-private';replace=document.os.replace
        def swap(*args,**kwargs):
            self.parent.rename(held);self.parent.symlink_to(outside,target_is_directory=True)
            return replace(*args,**kwargs)
        try:
            with mock.patch.object(document.os,'replace',side_effect=swap):
                with self.assertRaises((ValueError,Refused,StorageError)) as caught:document.write(self.path,{'format':1,'proof':'new'})
                if isinstance(caught.exception,StorageError):self.assertEqual(caught.exception.code,'unsafe_path')
            self.assertEqual(protected.read_bytes(),b'outside user bytes')
            self.assertEqual({p.name for p in outside.iterdir()},{'history.json'})
            self.assertEqual({p.name for p in held.iterdir()},{'history.json'})
        finally:
            if self.parent.is_symlink():self.parent.unlink();held.rename(self.parent)
        self.assertEqual(document.read(self.path),{'format':1,'proof':'new'})  # Unconfirmed publish stayed on original inode.


if __name__=='__main__':unittest.main()
