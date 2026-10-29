"""Actual pinned Controller aliases; preserve accepted credentials and local bytes."""
import io
import hashlib
import unittest
import uuid
from asc.node.enrollment import EnrollmentRefused
from asc.node.storage import NativeStorage
import test_native_enrollment as fixture


class NativeControllerChangeTests(unittest.TestCase):
    setUp=fixture.NativeEnrollmentTests.setUp
    join=fixture.NativeEnrollmentTests.join
    proxy=fixture.NativeEnrollmentTests.proxy

    def test_address_change_keeps_node_token_tls_volume_bytes_and_idempotent_record(self):
        self.join(); storage=NativeStorage(self.context);storage.configure(1024**2,0)
        before=self.context.load();volume=before['storage']['volume_id'];data=b'old native node bytes';sha=hashlib.sha256(data).hexdigest()
        with storage.open() as engine:
            row=engine.initiate('owner',volume,'rebind_native_01','retained.bin',len(data),sha)
            engine.upload(row['session_id'],'owner',volume,io.BytesIO(data),len(data));saved=engine.commit(row['session_id'],'owner',volume)
        _,_,origin=self.proxy()
        self.client.change_controller(origin,self.pin,self.cluster)
        after=self.context.load();expected=dict(before['node'],controller=origin)
        self.assertEqual(after['node'],expected)
        for key in ('app_id','context_id','tls','storage','pending','binding','device_binding'):
            self.assertEqual(before[key],after[key])
        raw=self.store.raw;self.client.change_controller(origin,self.pin,self.cluster);self.assertEqual(raw,self.store.raw)
        with storage.open() as engine:
            with engine.download(saved['file_id'],volume) as (_,stream):self.assertEqual(stream.read(),data)
        self.assertEqual(len(self.reg.snapshot()['nodes']),1)

    def test_wrong_identity_runtime_or_unreachable_alias_never_changes_record(self):
        self.join();raw=self.store.raw
        for pin,cluster in (('0'*64,self.cluster),(self.pin,str(uuid.uuid4()))):
            with self.assertRaises(EnrollmentRefused):self.client.change_controller(self.origin,pin,cluster)
            self.assertEqual(raw,self.store.raw)
        for override in ({'cluster_id':str(uuid.uuid4())},{'mode':'metadata-consensus-development','raft_enabled':True}):
            _,_,origin=self.proxy(override=override)
            with self.assertRaises(EnrollmentRefused):self.client.change_controller(origin,self.pin,self.cluster)
            self.assertEqual(raw,self.store.raw)

    def test_pending_join_cannot_be_rebound_or_replaced(self):
        proxy,_,origin=self.proxy(drop=True)
        with self.assertRaises(Exception):self.join(origin=origin)
        self.assertTrue(proxy.dropped);raw=self.store.raw
        with self.assertRaises(EnrollmentRefused):self.client.change_controller(self.origin,self.pin,self.cluster)
        self.assertEqual(raw,self.store.raw)
