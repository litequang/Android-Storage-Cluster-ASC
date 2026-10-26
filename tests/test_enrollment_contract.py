"""Shared host-independent client contract; actual TLS/lost-ACK coverage is retained."""
import copy
import json
import secrets
import unittest
from unittest.mock import patch
import uuid

from asc.client import ClientError
from asc.enrollment import new_pending, accepted_identity


class EnrollmentContractTests(unittest.TestCase):
    def pending(self, **kwargs):
        return new_pending('https://127.0.0.1:8443', 'a' * 64, str(uuid.uuid4()),
                           'shared contract fixture', {'protected': False},
                           secrets.token_hex(6).upper(), **kwargs)

    def test_same_legacy_format_independent_tokens_and_no_caller_mutation(self):
        profile = {'protected': False, 'nested': {'observed': None}}
        with patch('getpass.getpass', side_effect=AssertionError('no prompt')), \
                patch('subprocess.run', side_effect=AssertionError('no subprocess')):
            pending = new_pending('https://127.0.0.1:8443', 'a' * 64, str(uuid.uuid4()),
                                  'fixture', profile, secrets.token_hex(6).upper())
        self.assertEqual(set(pending), {'config_version', 'controller', 'pin', 'target_node_id',
                                       'cluster_id', 'expected_cluster_id', 'payload'})
        payload = pending['payload']
        self.assertEqual(set(payload), {'protocol_version', 'code', 'name', 'profile',
                                       'enrollment_id', 'enrollment_token'})
        self.assertEqual((pending['config_version'], payload['protocol_version']), (1, 1))
        self.assertNotEqual(payload['enrollment_id'], payload['enrollment_token'])
        self.assertEqual(len(payload['enrollment_id']), 43)
        profile['nested']['observed'] = True
        self.assertIsNone(payload['profile']['nested']['observed'])

    def test_original_pending_roundtrip_accepts_same_identity_and_never_embeds_code(self):
        pending = self.pending(); saved = json.dumps(pending); node = str(uuid.uuid4())
        reply = {'cluster_id': pending['expected_cluster_id'], 'node_id': node,
                 'token': pending['payload']['enrollment_token'], 'token_version': 1}
        first = accepted_identity(pending, reply)
        second = accepted_identity(json.loads(saved), copy.deepcopy(reply))
        self.assertEqual(first, second)
        self.assertEqual(first['node_id'], node)
        self.assertEqual(first['token'], pending['payload']['enrollment_token'])
        self.assertNotIn('code', first)
        self.assertNotIn('enrollment_id', first)
        self.assertEqual(json.dumps(pending), saved)

    def test_mismatched_cluster_target_or_token_preserves_pending_and_has_no_secret_error(self):
        target = str(uuid.uuid4()); cluster = str(uuid.uuid4())
        pending = self.pending(target=target, cluster=cluster)
        saved = json.dumps(pending)
        reply = {'cluster_id': pending['expected_cluster_id'], 'node_id': target,
                 'token': pending['payload']['enrollment_token'], 'token_version': 2}
        for field in ('cluster_id', 'node_id', 'token'):
            wrong = dict(reply, **{field: str(uuid.uuid4())})
            with self.assertRaises(ClientError) as error:
                accepted_identity(pending, wrong)
            self.assertNotIn(pending['payload']['enrollment_token'], str(error.exception))
            self.assertNotIn(pending['payload']['code'], str(error.exception))
            self.assertEqual(json.dumps(pending), saved)
        self.assertEqual(accepted_identity(pending, reply)['node_id'], target)

    def test_target_and_controller_list_keep_legacy_shape_without_aliases(self):
        endpoints = [{'origin': 'https://127.0.0.1:8443', 'pin': 'a' * 64}]
        target = str(uuid.uuid4()); cluster = str(uuid.uuid4())
        pending = self.pending(target=target, cluster=cluster, controllers=endpoints)
        self.assertEqual(pending['payload']['node_id'], target)
        self.assertEqual(pending['target_node_id'], target)
        self.assertEqual(pending['cluster_id'], cluster)
        self.assertEqual(pending['controllers'], endpoints)
        endpoints[0]['pin'] = 'b' * 64
        self.assertEqual(pending['controllers'][0]['pin'], 'a' * 64)
