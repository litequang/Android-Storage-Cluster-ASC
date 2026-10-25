"""Actual three-voter/cohost pinned TLS external backup qualification."""
import hashlib
import io
import json
from pathlib import Path
import time
import unittest

from asc.catalog.common import canonical, digest, uid
from asc.client import ClientError, request_json
from asc.external.engine import BackupEngine, load
from asc.external.local import LocalStore, Tree
from asc.external.source import PinnedSource
from tests import test_failover as fixture


class ExternalFixture:
    setUpClass=classmethod(fixture.FailoverTests.setUpClass.__func__)
    start=fixture.FailoverTests.start
    stop=fixture.FailoverTests.stop
    stop_all=fixture.FailoverTests.stop_all
    leader=fixture.FailoverTests.leader
    partition=fixture.FailoverTests.partition
    split=fixture.FailoverTests.split
    make_cluster=fixture.FailoverTests.make_cluster
    launch_python=fixture.FailoverTests.launch_python
    kill_python=fixture.FailoverTests.kill_python
    close_cluster=fixture.FailoverTests.close_cluster
    failure_diagnostics=fixture.FailoverTests.failure_diagnostics
    wait_ready=fixture.FailoverTests.wait_ready
    cached=fixture.FailoverTests.cached
    wait_job=fixture.FailoverTests.wait_job
    direct=fixture.FailoverTests.direct

    def wait_copies(self,file_id,count):
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            report=self.owner.request('GET','files/'+file_id+'?consistency=strong')
            if report['available_replicas']>=count:return report
            time.sleep(.25)
        self.fail('actual replicas not verified within existing budget')

    def external_store(self):
        dest=self.base/'private-external';dest.mkdir(mode=0o700)
        roots=[*self.homes,*(self.base/('volume-'+str(i)) for i in range(3))]
        return LocalStore.initialize(dest,roots),roots


class ExternalClusterTests(ExternalFixture,unittest.TestCase):
    def test_actual_strong_capture_tls_all_version_bytes_and_owner_boundaries(self):
        leader=self.make_cluster()
        self.owner.request('POST','backup/enable',{'request_id':uid()})
        originals={}
        for version in (1,2):
            data=(b'external-disaster-backup-v'+str(version).encode()+b'\0')*1000
            result=self.owner.upload(io.BytesIO(data),'dr/versions.bin','dr-actual-v'+str(version),'replicated_2',version)
            if result['job_state']!='COMPLETED':self.wait_job(result['job_id'])
            file_id=result['file']['file']['file_id'];self.wait_copies(file_id,2);originals[file_id]=data
        # Retained old version and snapshot/lifecycle are copied, not just latest heads.
        self.owner.request('POST','backup/snapshots',{'request_id':uid(),'copies':2})
        self.owner.request('POST','backup/delete',{'request_id':uid(),'file_id':next(iter(originals))})
        store,roots=self.external_store();source=PinnedSource(self.owner)
        result=BackupEngine(store).create(source,roots)
        folder=store.path/'completed'/result['backup_id']
        with Tree(folder) as tree:manifest,metadata,doc=load(tree)
        self.assertEqual(result['manifest_sha256'],digest(manifest));self.assertEqual(len(manifest['files']),2)
        for file_id,data in originals.items():
            actual=(folder/'objects'/(file_id+'.blob')).read_bytes()
            self.assertEqual(actual,data);self.assertEqual(hashlib.sha256(actual).hexdigest(),hashlib.sha256(data).hexdigest())
        self.assertIn('backup',doc);self.assertEqual(len(doc['backup']['snapshots']),1)
        for e,n in zip(self.endpoints,self.nodes):
            self.assertNotIn(e['token'].encode(),metadata);self.assertNotIn(n['token'].encode(),metadata)
        e=self.endpoints[self.wait_ready()]
        with self.assertRaises(ClientError) as node_denied:
            request_json(e['origin'],e['pin'],'POST','/catalog/v1/external/capture',{},self.nodes[0]['token'])
        self.assertEqual(node_denied.exception.status,401)
        with self.assertRaises(ClientError):request_json(e['origin'],'0'*64,'POST','/catalog/v1/external/capture',{},e['token'])
        with self.assertRaises(ClientError):self.owner.request('POST','external/read',{'cluster_id':self.cluster,'epoch':self.epoch,
            'file':{**manifest['files'][0],'sha256':'0'*64}})
        self.assertFalse((folder/'controller.json').exists());self.assertFalse((folder/'registry.sqlite3').exists())
        self.assertFalse(manifest['writer_recovery_supported'])
        print('3D TLS PASS: real quorum capture, retained versions/snapshot, exact bytes, node-owner isolation and wrong pin rejection',flush=True)
