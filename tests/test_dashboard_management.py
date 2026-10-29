"""Actual owner HTTPS -> canonical Node approval/lifecycle, no phones or mocks."""
import hashlib
from contextlib import closing
import http.client
import json
import sqlite3
import time
import unittest
import uuid

from asc.client import request_json, ClientError
from tests import test_demo_dashboard as fixture


def pending_node(f):
    """Actual new enrollment/Engine/heartbeat, deliberately no owner approval."""
    root = f.home / ('pending-dashboard-'+uuid.uuid4().hex)
    f.command(root, 'init', '--role', 'node', '--host', '127.0.0.1')
    pair = f.command(f.controller, 'pair')
    f.command(root, 'join', '--controller', f.origin, '--pin', f.pin,
              '--name', 'dashboard-pending-node', input=pair['code']+'\n')
    port = f.free_port()
    storage = f.command(root, 'storage-init', '--host', '127.0.0.1', '--port', str(port),
                        '--quota', str(8*1024**2), '--reserve', '0')
    cfg = json.loads((root/'node/node.json').read_bytes())
    process = f.start(root, 'run-node')
    f.wait_for(lambda: f.seen(cfg['node_id']))
    return dict(root=root, cfg=cfg, process=process, port=port, volume=storage['volume_id'], pin=storage['pin'])


class DashboardManagementTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.DashboardAPITests()
        self.addCleanup(self.f.doCleanups); self.f.setUp()
        self.node = self.f.nodes[1]
        self.node_id = self.node['cfg']['node_id']
        self.path = '/api/manage/v1/nodes/' + self.node_id

    def preview(self, action='approve', parameters=None):
        if parameters is None:
            parameters = dict(origin='https://127.0.0.1:'+str(self.node['port']), pin=self.node['pin'].replace(':','').lower(),
                              volume_ids=[self.node['volume']], failure_domain='owner-confirmed-phone')
        status, _, reply = self.f.http('POST', self.path+'/preview',
            dict(management_version=1, action=action, parameters=parameters))
        self.assertEqual(status, 201, reply)
        return reply

    def confirmation(self, preview):
        return dict(management_version=1, intent_sha256=preview['intent_sha256'],
                    confirmation_node_id=self.node_id, physical_domain_confirmed=True)

    def apply(self, preview, **changes):
        return self.f.http('POST', '/api/manage/v1/confirm/'+preview['preview_id'],
                           self.confirmation(preview) | changes)

    def approval(self):
        with closing(sqlite3.connect(self.f.controller/'controller/registry.sqlite3')) as db:
            db.row_factory = sqlite3.Row
            # Background real probes may update capabilities/checked_at while a
            # preview is open. Compare ALL administrative authority fields, not
            # unrelated live telemetry; no worker pause or clock manipulation.
            row = db.execute('SELECT node_id,origin,pin,device_id,volume_ids,metadata_allowed,storage_allowed,approved_generation '
                             'FROM catalog_nodes WHERE node_id=?', (self.node_id,)).fetchone()
            return dict(row) if row else None

    def test_new_enrolled_node_requires_explicit_web_approval_before_probed_storage(self):
        self.node = pending_node(self.f); self.node_id = self.node['cfg']['node_id']
        self.path = '/api/manage/v1/nodes/'+self.node_id
        self.assertIsNone(self.approval())
        status, _, detail = self.f.http('GET', self.path)
        self.assertEqual(status, 200)
        self.assertIsNone(detail['approval'])
        self.assertIn(self.node['volume'], detail['reported_volume_ids'])
        self.assertFalse(detail['reported_volumes_verified'])
        preview = self.preview()
        self.assertIsNone(self.approval())
        self.assertEqual(self.apply(preview)[0], 200)
        status, _, state = self.f.http('POST', '/api/refresh', {})
        self.assertEqual(status, 200)
        node = next(n for n in state['nodes'] if n['node_id'] == self.node_id)
        self.assertTrue(node['storage_approved'])
        self.assertTrue(node['volumes'][0]['writable'])
        self.assertTrue(node['volumes'][0]['readable'])

    def test_preview_no_mutation_confirm_and_replay_actual_two_replica_upload(self):
        before = self.approval()
        status, _, caps = self.f.http('GET', '/api/capabilities')
        self.assertEqual(status, 200); self.assertTrue(caps['node_management'])
        self.assertFalse(caps['physical_gc']); self.assertFalse(caps['recovery_writer'])
        status, _, detail = self.f.http('GET', self.path)
        self.assertEqual(status, 200); self.assertFalse(detail['reported_volumes_verified'])
        self.assertEqual(detail['node_id'], self.node_id)
        preview = self.preview()
        self.assertEqual(self.approval(), before)
        self.assertFalse(preview['storage_verified'])
        status, _, reply = self.apply(preview, physical_domain_confirmed=False)
        self.assertEqual((status, reply['error']), (409, 'management_confirmation_required'))
        self.assertEqual(self.approval(), before)
        status, _, reply = self.apply(preview)
        self.assertEqual(status, 200, reply); self.assertTrue(reply['applied'])
        self.assertFalse(reply['storage_verified'])
        status, _, replay = self.apply(preview)
        self.assertEqual(status, 200); self.assertTrue(replay['replayed'])
        self.assertEqual(self.approval()['device_id'], 'owner-confirmed-phone')
        self.assertEqual(self.node['cfg'], json.loads((self.node['root']/'node/node.json').read_bytes()))
        entry = self.f.upload()
        self.assertEqual(entry['available_replicas'], 2)
        status, headers, raw = self.f.http('GET', '/api/files/'+entry['file']['file_id']+'/content', json_response=False)
        self.assertEqual((status, raw), (200, self.f.data))
        self.assertEqual(headers['X-ASC-SHA256'], hashlib.sha256(raw).hexdigest())
        serialized = json.dumps([caps, detail, preview, reply, replay])
        for secret in (self.f.admin(), self.node['cfg']['token']):
            self.assertNotIn(secret, serialized)

    def test_owner_session_csrf_origin_and_confirmation_binding(self):
        preview = self.preview('rename', {'name':'new-safe-name'})
        payload = self.confirmation(preview)
        path = '/api/manage/v1/confirm/'+preview['preview_id']
        self.assertEqual(self.f.http('POST', path, payload, authenticated=False)[0], 401)
        self.assertEqual(self.f.http('POST', path, payload, headers={'X-ASC-CSRF':'wrong'})[0], 401)
        self.assertEqual(self.f.http('POST', path, payload, headers={'Origin':'https://evil.invalid'})[0], 403)
        self.assertEqual(self.apply(preview, confirmation_node_id=self.f.nodes[0]['cfg']['node_id'])[0], 409)
        self.assertEqual(self.apply(preview, intent_sha256='0'*64)[0], 409)
        self.f.login()  # New authenticated owner session does not own this preview.
        self.assertEqual(self.apply(preview)[0], 404)
        self.assertEqual(self.f.http('POST', self.path+'/preview',
            dict(management_version=1, action='approve', parameters={}), authenticated=False)[0], 401)

    def test_strict_input_public_endpoint_pin_and_unknown_actions_no_writes(self):
        before = self.approval()
        base = dict(origin='https://127.0.0.1:'+str(self.node['port']), pin='a'*64,
                    volume_ids=[self.node['volume']], failure_domain='test-phone')
        for changes in ({'origin':'http://127.0.0.1:9443'}, {'origin':'https://8.8.8.8:9443'},
                        {'pin':'no-pin'}, {'volume_ids':['../outside']}, {'volume_ids':[]},
                        {'volume_ids':[self.node['volume']]*2}, {'failure_domain':' bad '}, {'admin_token':'forbidden'}):
            status, _, _ = self.f.http('POST', self.path+'/preview',
                dict(management_version=1, action='approve', parameters=base | changes))
            self.assertIn(status, (400, 403), changes)
        for action in ('shell', 'gc', 'promote', 'quota', 'activate-recovery'):
            self.assertEqual(self.f.http('POST', self.path+'/preview',
                dict(management_version=1, action=action, parameters={}))[0], 400)
        self.assertEqual(self.f.http('POST', self.path+'/preview',
            dict(management_version=True, action='revoke', parameters={}))[0], 400)
        self.assertEqual(self.approval(), before)
        self.assertEqual(self.f.http('GET', '/api/manage/v1/nodes/local-controller')[0], 404)

    def test_stale_approval_cas_is_checked_inside_canonical_sql_transaction(self):
        preview = self.preview()
        current = self.approval()
        request_json(self.f.origin, self.f.pin, 'POST', '/catalog/v1/nodes/register',
            dict(node_id=self.node_id, device_id='concurrent-owner-domain', origin=current['origin'], pin=current['pin'],
                 volume_ids=json.loads(current['volume_ids'])), self.f.admin())
        status, _, reply = self.apply(preview)
        self.assertEqual((status, reply['error']), (409, 'node_state_changed'))
        self.assertEqual(self.approval()['device_id'], 'concurrent-owner-domain')

    def test_revoke_between_preview_and_confirm_rejects_stale_generation(self):
        preview = self.preview('rename', {'name':'must-not-be-applied'})
        request_json(self.f.origin, self.f.pin, 'POST', '/api/v1/admin/revoke', {'node_id':self.node_id}, self.f.admin())
        status, _, reply = self.apply(preview)
        self.assertEqual((status, reply['error']), (409, 'node_state_changed'))
        with closing(sqlite3.connect(self.f.controller/'controller/registry.sqlite3')) as db:
            self.assertNotEqual(db.execute('SELECT name FROM nodes WHERE node_id=?', (self.node_id,)).fetchone()[0], 'must-not-be-applied')

    def test_actual_rename_revoke_preserves_objects_and_download_uses_survivor(self):
        entry = self.f.upload()
        def objects():
            return {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                    for n in self.f.nodes for p in (n['root']/'node/data/objects').glob('*.blob')}
        before = objects(); self.assertGreaterEqual(len(before), 2)
        preview = self.preview('rename', {'name':'<img src=x onerror=alert(1)> owner name'})
        self.assertEqual(self.apply(preview)[0], 200)
        preview = self.preview('revoke', {})
        self.assertGreaterEqual(preview['recorded_replicas'], 1)
        self.assertEqual(self.apply(preview)[0], 200)
        status, _, raw = self.f.http('GET', '/api/files/'+entry['file']['file_id']+'/content', json_response=False)
        self.assertEqual((status, raw), (200, self.f.data))
        self.assertEqual(objects(), before)
        self.assertEqual(self.node['cfg'], json.loads((self.node['root']/'node/node.json').read_bytes()))

    def test_real_lost_ack_retry_and_restart_invalidates_preview_without_state_reset(self):
        preview = self.preview()
        connection = http.client.HTTPSConnection('127.0.0.1', self.f.dashboard_port, context=self.f.context, timeout=10)
        connection.request('POST', '/api/manage/v1/confirm/'+preview['preview_id'],
            body=json.dumps(self.confirmation(preview)), headers={'Origin':self.f.browser_origin,
                'Cookie':self.f.cookie, 'X-ASC-CSRF':self.f.csrf, 'Content-Type':'application/json'})
        connection.close()  # Successful TLS request; caller deliberately loses the actual ACK.
        self.f.wait_for(lambda:self.approval()['device_id']=='owner-confirmed-phone')
        status, _, reply = self.apply(preview)
        self.assertEqual(status, 200); self.assertTrue(reply['replayed'])
        other = self.preview('rename', {'name':'not-after-restart'})
        before = (self.f.controller/'controller/server.crt').read_bytes()
        self.f.stop(self.f.controller_process)
        self.f.controller_process = self.f.start(self.f.controller, 'run-controller'); self.f.login()
        self.assertEqual(self.apply(other)[0], 404)
        self.assertEqual((self.f.controller/'controller/server.crt').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
