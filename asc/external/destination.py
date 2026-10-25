"""Logical destination/provider boundary; only local POSIX adapter is implemented.

A future provider must implement these operations with equivalent immutable
conditional writes, privacy, resume/readback, independent manifest anchoring and
no-delete guarantees. It must not emulate local descriptors or silently fall back
from cloud storage to source disks. Provider credentials/key handling is separate.
"""
from typing import Protocol
from .local import LocalStore
from .engine import BackupEngine
from .verify import inventory, verify, retention_preview
from .recovery import stage


class Destination(Protocol):
    def initialize(self, source_roots): ...
    def create(self, source, source_roots): ...
    def resume(self, source, backup_id, source_roots): ...
    def inventory(self): ...
    def verify(self, backup_id, expected_sha256, minimum_index=0, cluster_id=None): ...
    def retention_preview(self): ...
    def stage(self, backup_id, expected_sha256, destination, source_roots, cluster_id, minimum_index): ...


class LocalDirectory:
    """Approved private local/mounted directory; mount semantics need qualification."""
    def __init__(self, path):self.store=LocalStore(path)
    def initialize(self, source_roots):LocalStore.initialize(self.store.path,source_roots)
    def create(self, source, source_roots):return BackupEngine(self.store).create(source,source_roots)
    def resume(self, source, backup_id, source_roots):return BackupEngine(self.store).resume(source,backup_id,source_roots)
    def inventory(self):return inventory(self.store)
    def verify(self, backup_id, expected_sha256, minimum_index=0, cluster_id=None):
        return verify(self.store,backup_id,expected_sha256,minimum_index,cluster_id)
    def retention_preview(self):return retention_preview(self.store)
    def stage(self, backup_id, expected_sha256, destination, source_roots, cluster_id, minimum_index):
        return stage(self.store,backup_id,expected_sha256,destination,source_roots,cluster_id,minimum_index)
