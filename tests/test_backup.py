"""Phase 3A projection/retention semantics, plus actual Windows Raft/TLS fault simulation."""
import copy
from contextlib import contextmanager
import hashlib
import io
import json
import ssl
from pathlib import Path
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock
from urllib.parse import quote

from asc.backup import state as backup_state
from asc.backup.service import Backups
from asc.catalog.common import CatalogError, canonical, digest, uid
from asc.catalog.state import Catalog, insert
from asc.client import ClientError
from asc.failover import state
from tests import test_failover as fixture


class ProjectionRuntime:
    """Unit-only commit boundary; actual quorum/fault acceptance is below."""
    def __init__(self, doc):
        self.doc = copy.deepcopy(doc)
        self.lock = threading.RLock()
        self.index = 100
        self.crash = False

    def view(self):
        return {'document': copy.deepcopy(self.doc), 'state': {'index': self.index, 'term': 4}}

    @contextmanager
    def operation(self):
        yield self.view()

    def commit(self, view, doc, *args):
        state.validate(doc)
        self.doc = copy.deepcopy(doc); self.index += 1
        if self.crash:
            self.crash = False
            raise fixture.helpers.SimulatedCrash()


class BackupStateTests(unittest.TestCase):
    def setUp(self):
        self.reg = state.MemoryRegistry(uid()); self.addCleanup(self.reg.db.close)
        self.catalog = Catalog(self.reg)
        self.ids = []
        for version in (1, 2):
            file_id = uid(); self.ids.append(file_id)
            insert(self.reg.db, 'catalog_files', {'file_id': file_id, 'logical_path': 'history/file.bin',
                'version': version, 'size': 3, 'sha256': hashlib.sha256(b'old' if version == 1 else b'new').hexdigest(),
                'policy': 'single', 'created_at': 10, 'updated_at': 10, 'revision': 0,
                'upload_key': 'unit-version-'+str(version), 'upload_policy': 'single'})
            insert(self.reg.db, 'catalog_replicas', {'replica_id': uid(), 'file_id': file_id, 'node_id': uid(),
                'volume_id': uid(), 'local_file_id': uid(), 'state': 'VERIFIED', 'created_at': 10,
                'updated_at': 10, 'verified_at': 10})
            self.catalog._event(self.reg.db, file_id)
        self.runtime = ProjectionRuntime(state.export(self.reg.db, 1, {'node_id': 'voter-a', 'term': 4}))
        self.backups = Backups(SimpleNamespace(runtime=self.runtime, timeout=300))
        self.backups.enable({'request_id': 'unit-enable-001'})

    def call(self, action, **obj):
        return getattr(self.backups, action)({'request_id': uid(), **obj})

    def test_snapshot_binds_exact_committed_source_and_history_is_immutable(self):
        before = self.runtime.view()
        result = self.call('snapshot', copies=2)
        snapshot = self.runtime.doc['backup']['snapshots'][result['snapshot_id']]
        manifest = snapshot['manifest']
        self.assertEqual(manifest['source_index'], before['state']['index'])
        self.assertEqual(manifest['control_revision'], before['document']['revision'])
        self.assertEqual(manifest['catalog_revision'], before['document']['catalog']['revision'])
        self.assertEqual(snapshot['manifest_sha256'], digest(manifest))
        self.assertEqual([f['file_id'] for f in manifest['files']], [self.ids[1]])
        self.assertEqual(len(self.backups.inspect('history', 'history/file.bin')['versions']), 2)
        self.call('delete', file_id=self.ids[1])
        self.assertEqual(self.runtime.doc['backup']['snapshots'][result['snapshot_id']], snapshot)
        empty = self.call('snapshot')
        self.assertEqual(self.runtime.doc['backup']['snapshots'][empty['snapshot_id']]['files'], [])

    def test_lost_commit_ack_replays_same_result_and_rejects_changed_intent(self):
        obj = {'request_id': 'unit-lost-ack-001', 'copies': 1}
        self.runtime.crash = True
        with self.assertRaises(fixture.helpers.SimulatedCrash):
            self.backups.snapshot(obj)
        original = copy.deepcopy(self.runtime.doc['backup'])
        result = self.backups.snapshot(obj)
        self.assertIn(result['job_id'], original['jobs'])
        self.assertEqual(self.runtime.doc['backup'], original)
        with self.assertRaises(CatalogError):
            self.backups.snapshot({**obj, 'copies': 2})

    def test_softdelete_retention_and_snapshot_pin_preserve_bytes_and_metadata(self):
        snapshot = self.call('snapshot', retention_seconds=60)
        file_id = self.ids[1]
        self.call('policy', logical_path='history/file.bin', keep_last=1, max_age_seconds=60, trash_seconds=60)
        with mock.patch('asc.backup.service.now', return_value=1000):
            self.call('delete', file_id=file_id)
        # Keep snapshot retained even when a long-running backup is overdue.
        with mock.patch('asc.backup.service.now', return_value=2000):
            result = self.call('retention')
        self.assertEqual(result['physical_deletions'], 0)
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], file_id), 'TRASH')
        self.assertIn(self.ids[0], result['expired_versions'])
        with mock.patch('asc.backup.service.now', return_value=2001):
            restore = self.call('restore', file_id=file_id, snapshot_id=snapshot['snapshot_id'])
        self.assertEqual(restore['target_version'], 3)
        self.assertEqual(len(self.runtime.doc['catalog']['files']), 2)

    def test_expired_versions_reject_restore_and_latest_live_head_is_protected(self):
        self.call('policy', logical_path='history/file.bin', keep_last=1, max_age_seconds=60, trash_seconds=60)
        with mock.patch('asc.backup.service.now', return_value=10000000000):
            self.call('retention')
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], self.ids[0]), 'EXPIRED')
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], self.ids[1]), 'LIVE')
        with self.assertRaises(CatalogError):
            self.call('restore', file_id=self.ids[0])

    def test_restore_reserves_distinct_versions_for_concurrent_requests(self):
        first = self.call('restore', file_id=self.ids[0])
        second = self.call('restore', file_id=self.ids[0])
        self.assertEqual((first['target_version'], second['target_version']), (3, 4))
        self.assertNotEqual(first['job_id'], second['job_id'])

    def test_takeover_fences_running_and_checkpointed_jobs_and_retains_source_pins(self):
        result = self.call('snapshot')
        job_id = result['job_id']
        self.backups._claim(job_id)
        before = copy.deepcopy(self.runtime.doc)
        taken = state.takeover(before, 'voter-b', 5)
        job = taken['backup']['jobs'][job_id]
        self.assertEqual(job['state'], 'RETRY')
        self.assertIsNone(job['run_token'])
        self.assertIsNone(job['lease_until'])
        self.assertEqual(job['proofs'], [])
        self.assertEqual(taken['backup']['snapshots'], before['backup']['snapshots'])
        self.assertEqual(backup_state.pinned(taken['backup']), {self.ids[1]})

    def test_corrupt_manifest_and_future_schema_never_install(self):
        result = self.call('snapshot')
        for mutate in (lambda d: d['backup']['snapshots'][result['snapshot_id']]['manifest']['files'][0].update(sha256='0'*64),
                       lambda d: d['backup'].update(schema=2),
                       lambda d: d['backup']['files'].update({uid(): {'state': 'TRASH', 'changed_at': 1, 'retain_until': 2}})):
            doc = copy.deepcopy(self.runtime.doc); mutate(doc)
            with self.assertRaises(CatalogError):
                state.prepare_registry(doc)

    def test_runtime_sql_preparation_roundtrip_cannot_lose_backup_state(self):
        self.call('snapshot')
        doc = self.runtime.doc
        reg = state.prepare_registry(doc)
        try:
            self.assertEqual(state.export(reg.db, doc['revision'], doc['authority']), doc)
        finally:
            reg.db.close()

    def test_scheduler_due_tick_is_atomic_and_disabled_schedule_stays_idle(self):
        with mock.patch('asc.backup.service.now', return_value=1000):
            schedule = self.call('schedule', interval_seconds=60, copies=1)
            created = self.backups._scheduled()
            self.assertIn(created['snapshot_id'], self.runtime.doc['backup']['snapshots'])
            self.assertEqual(self.backups._scheduled(), {})
        schedule_id = schedule['schedule_id']
        self.backups.configure_schedule(schedule_id, {'request_id': uid(), 'enabled': False})
        with mock.patch('asc.backup.service.now', return_value=2000):
            self.assertEqual(self.backups._scheduled(), {})

    def test_snapshot_refuses_unverified_latest_upload_instead_of_silently_using_old_version(self):
        self.runtime.doc['catalog']['replicas'] = []
        # Keep Catalog event consistency while creating an unverified head.
        self.runtime.doc['catalog']['events'][-1]['payload']['replicas'] = []
        event = self.runtime.doc['catalog']['events'][-1]
        event['digest'] = digest({k: v for k, v in event.items() if k != 'digest'})
        self.runtime.doc['catalog']['head_digest'] = event['digest']
        with self.assertRaises(CatalogError) as rejected:
            self.call('snapshot')
        self.assertEqual(rejected.exception.code, 'snapshot_unverified_head')


    def test_due_schedule_defers_unverified_head_without_starving_existing_work(self):
        self.call('schedule', interval_seconds=60)
        reg = state.prepare_registry(self.runtime.doc)
        try:
            reg.db.execute('DELETE FROM catalog_replicas')
            for file_id in self.ids:
                Catalog(reg)._event(reg.db, file_id)
            self.runtime.doc = state.export(reg.db, self.runtime.doc['revision']+1, self.runtime.doc['authority'])
        finally:
            reg.db.close()
        result = self.backups._scheduled()
        self.assertEqual(result, {'deferred': True})
        schedule = next(iter(self.runtime.doc['backup']['schedules'].values()))
        self.assertEqual(schedule['last_error'], 'snapshot_unverified_head')
        self.assertEqual(self.runtime.doc['backup']['jobs'], {})

    def test_pending_new_upload_cannot_expire_last_verified_version(self):
        reg = state.prepare_registry(self.runtime.doc)
        try:
            reg.db.execute('DELETE FROM catalog_replicas WHERE file_id=?', (self.ids[1],))
            Catalog(reg)._event(reg.db, self.ids[1])
            self.runtime.doc = state.export(reg.db, self.runtime.doc['revision']+1, self.runtime.doc['authority'])
        finally:
            reg.db.close()
        self.call('policy', logical_path='history/file.bin', keep_last=1, max_age_seconds=60, trash_seconds=60)
        with mock.patch('asc.backup.service.now', return_value=10000000000):
            self.call('retention')
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], self.ids[0]), 'LIVE')
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], self.ids[1]), 'LIVE')

    def test_maximum_request_id_fits_go_receipt_key_and_replays(self):
        obj = {'request_id': 'a'*128}
        with mock.patch.object(self.runtime, 'commit', wraps=self.runtime.commit) as commit:
            result = self.backups.snapshot(obj)
            self.assertLessEqual(len(commit.call_args.args[2]), 128)
        self.assertEqual(self.backups.snapshot(obj), result)

    def test_bad_retention_bounds_are_rejected_without_mutating_authority(self):
        before = copy.deepcopy(self.runtime.doc)
        for row in ({'keep_last': 0, 'max_age_seconds': 60, 'trash_seconds': 60},
                    {'keep_last': 1, 'max_age_seconds': True, 'trash_seconds': 60},
                    {'keep_last': 1, 'max_age_seconds': 60, 'trash_seconds': -1}):
            with self.assertRaises((CatalogError, ValueError)):
                self.call('policy', logical_path='history/file.bin', **row)
            self.assertEqual(self.runtime.doc, before)

    def test_empty_snapshot_can_complete_without_claiming_any_file_bytes(self):
        self.call('delete', file_id=self.ids[1])
        result = self.call('snapshot')
        job = self.backups._claim(result['job_id'])
        self.backups._checkpoint(job, {'state': 'COMPLETED'})
        snapshot = self.runtime.doc['backup']['snapshots'][result['snapshot_id']]
        self.assertEqual(snapshot['state'], 'VERIFIED')
        self.assertEqual(snapshot['files'], [])
        self.assertEqual(self.runtime.doc['backup']['jobs'][result['job_id']]['proofs'], [])

    def test_completion_without_independent_checksums_is_rejected(self):
        result = self.call('snapshot', copies=2)
        job = self.backups._claim(result['job_id'])
        before = copy.deepcopy(self.runtime.doc)
        with self.assertRaises(CatalogError):
            self.backups._checkpoint(job, {'state': 'COMPLETED'})
        self.assertEqual(self.runtime.doc, before)
        file = next(f for f in before['catalog']['files'] if f['file_id'] == self.ids[1])
        proof = {'file_id': file['file_id'], 'size': file['size'], 'sha256': file['sha256'],
                 'domains': ['same-device'], 'verified_at': 1}
        with self.assertRaises(CatalogError):
            self.backups._checkpoint(job, {'state': 'RETRY', 'cursor': 1, 'proofs': [proof]})
        self.assertEqual(self.runtime.doc, before)

    def test_stale_lease_cannot_complete_after_takeover(self):
        result = self.call('snapshot')
        job = self.backups._claim(result['job_id'])
        self.runtime.doc = state.takeover(self.runtime.doc, 'voter-b', 5)
        before = copy.deepcopy(self.runtime.doc)
        with self.assertRaises(CatalogError) as denied:
            self.backups._checkpoint(job, {'state': 'COMPLETED'})
        self.assertEqual(denied.exception.code, 'stale_backup_lease')
        self.assertEqual(self.runtime.doc, before)

    def test_projection_limits_fail_closed_without_evicting_receipts(self):
        for i in range(backup_state.LIMITS['requests']-1):
            self.runtime.doc['backup']['requests']['fake-request-'+str(i)] = {'intent': '0'*64, 'result': {}}
        before = copy.deepcopy(self.runtime.doc)
        with self.assertRaises(CatalogError):
            self.call('snapshot')
        self.assertEqual(self.runtime.doc, before)

    def test_retained_snapshot_restore_batch_reserves_each_target_once(self):
        snapshot = self.call('snapshot')
        obj = {'request_id': 'unit-batch-restore-001'}
        first = self.backups.restore_snapshot(snapshot['snapshot_id'], obj)
        self.assertEqual(self.backups.restore_snapshot(snapshot['snapshot_id'], obj), first)
        self.assertEqual(len(first['jobs']), 1)
        self.assertEqual(first['jobs'][0]['target_version'], 3)

    def test_trash_expiry_waits_for_active_restore_pin(self):
        with mock.patch('asc.backup.service.now', return_value=1000):
            self.call('policy', logical_path='history/file.bin', keep_last=1, max_age_seconds=60, trash_seconds=60)
            self.call('delete', file_id=self.ids[1])
            restore = self.call('restore', file_id=self.ids[1])
        with mock.patch('asc.backup.service.now', return_value=2000):
            self.call('retention')
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], self.ids[1]), 'TRASH')
        self.runtime.doc['backup']['jobs'][restore['job_id']]['state'] = 'FAILED'
        with mock.patch('asc.backup.service.now', return_value=2001):
            self.call('retention')
        self.assertEqual(backup_state.status(self.runtime.doc['backup'], self.ids[1]), 'EXPIRED')


class BackupClusterTests(unittest.TestCase):
    # Reuse the accepted fixture without inheriting/rerunning its test methods.
    setUpClass = classmethod(fixture.FailoverTests.setUpClass.__func__)
    start = fixture.FailoverTests.start
    stop = fixture.FailoverTests.stop
    stop_all = fixture.FailoverTests.stop_all
    leader = fixture.FailoverTests.leader
    partition = fixture.FailoverTests.partition
    split = fixture.FailoverTests.split
    make_cluster = fixture.FailoverTests.make_cluster
    launch_python = fixture.FailoverTests.launch_python
    kill_python = fixture.FailoverTests.kill_python
    close_cluster = fixture.FailoverTests.close_cluster
    failure_diagnostics = fixture.FailoverTests.failure_diagnostics
    wait_ready = fixture.FailoverTests.wait_ready
    cached = fixture.FailoverTests.cached
    wait_job = fixture.FailoverTests.wait_job
    direct = fixture.FailoverTests.direct

    def post(self, path, **obj):
        return self.owner.request('POST', 'backup/'+path, {'request_id': uid(), **obj})

    def backup_job(self, job_id):
        return self.owner.request('GET', 'backup/jobs')['jobs'][job_id]

    def wait_backup(self, job_id, timeout=240):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            job = self.backup_job(job_id)
            if job['state'] == 'COMPLETED':
                return job
            self.assertNotEqual(job['state'], 'FAILED', job)
            time.sleep(0.4)
        self.fail('backup/restore job recovery exceeded acceptance budget: '+str(job))

    def mark(self, number, label):
        print(f'\nPhase 3A {number:02d} PASS: {label}', flush=True)

    def upload(self, data, path, version):
        result = self.owner.upload(io.BytesIO(data), path, 'phase3a-upload-'+str(version), 'replicated_2', version)
        if result['job_state'] != 'COMPLETED':
            self.wait_job(result['job_id'])
        file_id = result['file']['file']['file_id']
        deadline = time.monotonic()+180
        while time.monotonic() < deadline:
            report = self.owner.request('GET', 'files/'+file_id+'?consistency=strong')
            if report['available_replicas'] >= 2:
                return file_id
            time.sleep(0.4)
        self.fail('two independent verified replicas were not produced')

    def install_commit_proxies(self, leader):
        proxies = []
        for index, home in enumerate(self.homes):
            node = next(n for n in self.cached(leader)['document']['tables']['catalog_nodes'] if n['node_id'] == self.nodes[index]['node_id'])
            proxy = fixture.Server(('127.0.0.1', 0), None, '', fixture.LostAckProxy)
            proxy.upstream, proxy.pin = node['origin'], node['pin']
            proxy.drop, proxy.dropped = threading.Event(), threading.Event()
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(home/'storage.crt', home/'storage.key')
            proxy.tls_context = context
            thread = threading.Thread(target=proxy.serve_forever, daemon=True); thread.start()
            self.addCleanup(lambda p=proxy, t=thread: (p.shutdown(), p.server_close(), t.join(timeout=5)))
            origin = 'https://127.0.0.1:'+str(proxy.server_address[1])
            self.owner.request('POST', 'nodes/register', {'node_id': node['node_id'], 'origin': origin,
                'pin': node['pin'], 'device_id': node['device_id'], 'volume_ids': json.loads(node['volume_ids'])})
            proxies.append(proxy)
        for proxy in proxies:
            proxy.drop.set()
        return proxies

    def test_windows_backup_restore_fault_matrix(self):
        leader = self.make_cluster()
        self.post('enable')
        self.mark(1, 'existing three-Go/three-Python/TLS cluster explicitly enables backup projection')
        path = 'phase3a/history.bin'
        old, new = b'fake old backup bytes\0'*64, b'fake new backup bytes\0'*64
        first = self.upload(old, path, 1)
        snapshot = self.post('snapshots', copies=2)
        completed = self.wait_backup(snapshot['job_id'])
        self.assertEqual(len(completed['proofs'][0]['domains']), 2)
        snap = self.owner.request('GET', 'backup/snapshots')['snapshots'][snapshot['snapshot_id']]
        self.assertEqual(snap['manifest_sha256'], digest(snap['manifest']))
        self.assertLess(snap['manifest']['source_index'], self.cached(leader)['state']['index'])
        self.assertEqual(snap['files'][0]['file_id'], first)
        self.mark(2, 'committed-index snapshot and independent streamed checksum proof on two domains')
        second = self.upload(new, path, 2)
        history = self.owner.request('GET', 'backup/history?logical_path='+quote(path, safe=''))['versions']
        self.assertEqual([f['file']['version'] for f in history], [2, 1])
        self.post('delete', file_id=second)
        self.assertIn(second, self.owner.request('GET', 'backup/trash')['trash'])
        with self.assertRaises(ClientError):
            self.owner.download(second, io.BytesIO())
        self.mark(3, 'history and accidental soft delete preserve source and deny normal deleted-version download')
        restore_obj = {'request_id': 'phase3a-restore-old-001', 'file_id': first, 'snapshot_id': snapshot['snapshot_id']}
        restored = self.owner.request('POST', 'backup/restore', restore_obj)
        again = self.owner.request('POST', 'backup/restore', restore_obj)
        self.assertEqual(again['job_id'], restored['job_id'])
        job = self.wait_backup(restored['job_id'])
        self.assertEqual(job['target_version'], 3)
        output = io.BytesIO(); self.owner.download(job['target_file_id'], output)
        self.assertEqual(output.getvalue(), old)
        self.assertNotIn(job['target_file_id'], (first, second))
        self.mark(4, 'old version restores into new immutable version with idempotent retry and exact bytes')
        # Drop an actual successful restore target commit ACK, then crash its Controller.
        proxies = self.install_commit_proxies(leader)
        crash_restore = self.post('restore', file_id=first, snapshot_id=snapshot['snapshot_id'])
        deadline = time.monotonic()+150
        while time.monotonic() < deadline and not any(p.dropped.is_set() for p in proxies):
            time.sleep(0.02)
        self.assertTrue(any(p.dropped.is_set() for p in proxies), 'actual successful target commit ACK must be lost')
        for proxy in proxies:
            proxy.drop.clear()
        old_controller = leader
        self.kill_python(old_controller)
        leader = self.wait_ready(exclude=(old_controller,))
        self.stop(old_controller); self.start(old_controller); self.launch_python(old_controller)
        job = self.wait_backup(crash_restore['job_id'])
        self.assertEqual(job['target_version'], 4)
        output = io.BytesIO(); self.owner.download(job['target_file_id'], output)
        self.assertEqual(output.getvalue(), old)
        doc = self.cached(leader)['document']
        matches = [f for f in doc['catalog']['files'] if f['upload_key'] == 'restore-'+crash_restore['job_id']]
        self.assertEqual(len(matches), 1)
        upload_jobs = [j for j in doc['tables']['catalog_jobs'] if j['file_id'] == matches[0]['file_id'] and j['kind'] == 'UPLOAD']
        self.assertEqual(len(upload_jobs), 1)
        fixture.FailoverTests.physical_job_state(self, upload_jobs[0], old)
        self.mark(5, 'actual lost target commit ACK plus Controller crash resumes one restore job/session/object/version')
        # A due schedule is durably captured once and survives Controller changes.
        schedule = self.post('schedules', interval_seconds=86400, copies=2)
        deadline = time.monotonic()+60
        while time.monotonic() < deadline:
            jobs = self.owner.request('GET', 'backup/jobs')['jobs']
            scheduled = [(j, row) for j, row in jobs.items() if row['kind'] == 'BACKUP' and j != snapshot['job_id']]
            if scheduled:
                break
            time.sleep(0.2)
        self.assertEqual(len(scheduled), 1)
        # Kill Python only. Its armed Go watchdog must withdraw before takeover.
        old_leader = leader
        self.kill_python(old_leader)
        leader = self.wait_ready(exclude=(old_leader,))
        self.assertNotEqual(leader, old_leader)
        self.wait_backup(scheduled[0][0])
        self.assertIn(schedule['schedule_id'], self.owner.request('GET', 'backup/schedules')['schedules'])
        self.mark(6, 'scheduled job and immutable snapshot recover after Python Leader crash and automatic failover')
        # Restart retained former Leader as follower, preserving all identities/state.
        self.stop(old_leader); self.start(old_leader); self.launch_python(old_leader)
        self.wait_ready()
        with self.assertRaises(ClientError):
            self.direct(old_leader, 'POST', '/catalog/v1/backup/delete', {'request_id': uid(), 'file_id': first})
        self.mark(7, 'former Leader cannot soft-delete under stale authority')
        # Partition all voters: every destructive logical mutation must fail.
        self.split([{0}, {1}, {2}])
        time.sleep(4)
        for i in range(3):
            with self.assertRaises(ClientError):
                self.direct(i, 'POST', '/catalog/v1/backup/delete', {'request_id': uid(), 'file_id': first})
        self.split([set(range(3))]); leader = self.wait_ready()
        output = io.BytesIO(); self.owner.download(first, output); self.assertEqual(output.getvalue(), old)
        self.mark(8, 'quorum loss rejects delete on every Controller and retains recoverable bytes')
        # Actual Go snapshot and full process restart preserve backup manifest/jobs.
        snapshot_success = False
        for client in self.clients:
            try:
                client.request('POST', '/v1/snapshot', {})
                snapshot_success = True
            except CatalogError:
                pass
        self.assertTrue(snapshot_success, 'at least one actual Go snapshot must complete')
        saved = self.owner.request('GET', 'backup/snapshots')['snapshots'][snapshot['snapshot_id']]
        for i in range(3):
            self.kill_python(i)
        self.stop_all()
        for i in range(3):
            self.start(i)
        for i in range(3):
            self.launch_python(i)
        leader = self.wait_ready()
        self.assertEqual(self.owner.request('GET', 'backup/snapshots')['snapshots'][snapshot['snapshot_id']], saved)
        self.mark(9, 'Go snapshot/replay and complete process restart preserve committed backup metadata')
        # Corrupt one actual retained body. Restore must find a healthy independent source.
        report = self.owner.request('GET', 'files/'+first+'?consistency=strong')
        replica = next(r for r in report['replicas'] if r['state'] == 'VERIFIED')
        index = next(i for i, n in enumerate(self.nodes) if n['node_id'] == replica['node_id'])
        blob = self.base/('volume-'+str(index))/'objects'/(replica['local_file_id']+'.blob')
        self.assertTrue(blob.is_file())
        blob.write_bytes(b'X'*len(old))
        recovered = self.post('restore', file_id=first, snapshot_id=snapshot['snapshot_id'])
        job = self.wait_backup(recovered['job_id'])
        output = io.BytesIO(); self.owner.download(job['target_file_id'], output)
        self.assertEqual(output.getvalue(), old)
        self.assertEqual(blob.read_bytes(), b'X'*len(old), 'suspect source must be retained')
        self.mark(10, 'corrupt source checksum is rejected; independent source restores exact bytes without deleting evidence')
        # Snapshot content must never be changed by newer versions/retention.
        self.post('policies', logical_path=path, keep_last=1, max_age_seconds=60, trash_seconds=60)
        retention = self.post('retention/run')
        self.assertEqual(retention['physical_deletions'], 0)
        self.assertEqual(self.owner.request('GET', 'backup/snapshots')['snapshots'][snapshot['snapshot_id']]['manifest'], saved['manifest'])
        self.mark(11, 'retention preserves snapshot-pinned versions and never physically deletes objects')
        # Corrupt every remaining physical source of one retained version. No
        # restore may fabricate success, even though its logical descriptor exists.
        report = self.owner.request('GET', 'files/'+first+'?consistency=strong')
        damaged = []
        for replica in report['replicas']:
            index = next(i for i, n in enumerate(self.nodes) if n['node_id'] == replica['node_id'])
            blob = self.base/('volume-'+str(index))/'objects'/(replica['local_file_id']+'.blob')
            if blob.is_file():
                blob.write_bytes(b'Z'*len(old)); damaged.append(blob)
        self.assertGreaterEqual(len(damaged), 2)
        impossible = self.post('restore', file_id=first, snapshot_id=snapshot['snapshot_id'])
        deadline = time.monotonic()+180
        while time.monotonic() < deadline:
            failed = self.backup_job(impossible['job_id'])
            self.assertNotEqual(failed['state'], 'COMPLETED', 'all corrupt sources cannot produce a successful restore')
            if failed['state'] == 'FAILED':
                break
            time.sleep(0.4)
        self.assertEqual(failed['state'], 'FAILED')
        self.assertEqual(failed['attempts'], 5)
        self.assertEqual(failed['proofs'], [])
        for blob in damaged:
            self.assertEqual(blob.read_bytes(), b'Z'*len(old))
        self.mark(12, 'all corrupt sources exhaust bounded retries without false restore proof or deleting evidence')



if __name__ == '__main__':
    unittest.main()
