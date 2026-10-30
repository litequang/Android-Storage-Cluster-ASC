"""Access-plane exclusions must hold independently of private-network reachability."""
import unittest
from asc.access.policy import Profile, private_origin, MAX_BODY

FILE = '12345678-1234-1234-1234-123456789abc'


def profile(**changes):
    return dict(format=1, mode='private-gateway', frontend_origin='https://100.100.1.2:8445',
                upstream_origin='https://127.0.0.1:8444', upstream_pin='a'*64,
                upstream_mode='single-writer-demo', max_body_bytes=MAX_BODY, **changes)


class AccessPolicyTests(unittest.TestCase):
    def test_numeric_private_ingress_is_not_evidence_of_vpn_or_authority(self):
        for origin in ('https://127.0.0.1:8445', 'https://192.168.1.2:8445', 'https://100.64.0.1:8445'):
            value=profile();value['frontend_origin']=origin
            result=Profile.parse(value).public()
            self.assertFalse(result['writer_authority'])
            self.assertEqual((result['vpn_membership'],result['remote_reachability']),('UNKNOWN','UNKNOWN'))
            self.assertFalse(result['production_accepted'])

    def test_public_wildcard_dns_and_ambiguous_origins_refuse(self):
        for origin in ('http://127.0.0.1:8445','https://0.0.0.0:8445','https://8.8.8.8:8445',
                       'https://169.254.1.2:8445','https://100.128.0.1:8445','https://example.com:8445',
                       'https://[::]:8445','https://127.0.0.1:443','https://127.0.0.1:8445/',
                       'https://u:p@127.0.0.1:8445','https://127.0.0.1:8445?x=1'):
            with self.subTest(origin=origin),self.assertRaises(ValueError):private_origin(origin)

    def test_no_implicit_mode_upgrade_or_config_secret_fields(self):
        for key,value in (('format',True),('format',2),('mode','cloudflare'),('upstream_mode','leader'),
                          ('upstream_origin','https://example.com:8444'),('upstream_pin',''),
                          ('max_body_bytes',True),('max_body_bytes',MAX_BODY+1)):
            raw=profile();raw[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):Profile.parse(raw)
        raw=profile();raw['admin_token']='must not be accepted'
        with self.assertRaises(ValueError):Profile.parse(raw)
        raw=profile();raw['frontend_origin']=raw['upstream_origin']
        with self.assertRaises(ValueError):Profile.parse(raw)

    def test_owner_file_manager_routes_use_existing_paths(self):
        p=Profile.parse(profile())
        for method,path in [('GET','/'),('GET','/api/state'),('POST','/api/login'),('POST','/api/uploads'),
                            ('POST','/api/files/query'),('POST','/api/jobs/query'),('GET','/api/jobs/'+FILE),
                            ('PUT','/api/uploads/'+FILE),('GET','/api/files/'+FILE+'/content')]:
            with self.subTest(method=method,path=path):self.assertTrue(p.permits(method,path))

    def test_observer_and_recovery_are_read_only_even_with_owner_session(self):
        for mode in ('core-quorum','recovery-read-only'):
            raw=profile();raw['upstream_mode']=mode;p=Profile.parse(raw)
            for method,path in [('POST','/api/uploads'),('POST','/api/refresh'),('PUT','/api/uploads/'+FILE),
                                ('POST','/api/files/query'),('POST','/api/jobs/query'),('GET','/api/jobs/'+FILE),
                                ('GET','/api/files/'+FILE+'/content'),('POST','/api/v1/quick-join/pairings')]:
                with self.subTest(mode=mode,path=path):self.assertFalse(p.permits(method,path))
            self.assertTrue(p.permits('POST','/api/login'));self.assertTrue(p.permits('GET','/api/state'))

    def test_never_expose_storage_management_shell_or_destructive_paths(self):
        p=Profile.parse(profile())
        for path in ('/api/v1/nodes','/api/v1/storage','/storage/v1/files','/api/v1/quick-join/pairings',
                     '/api/jobs/'+FILE+'/retry',
                     '/api/approve','/api/gc','/api/activate','/api/shell','/api/update','/api/files/'+FILE):
            with self.subTest(path=path):self.assertFalse(p.permits('DELETE',path));self.assertFalse(p.permits('POST',path))

    def test_encoded_paths_traversal_queries_and_absolute_uris_refuse(self):
        p=Profile.parse(profile())
        for path in ('/%61pi/state','/api/state?token=secret','/api/state#x','//api/state','/x/../api/state',
                     '/api/./state','/api\\state','https://127.0.0.1:8444/api/state','/api/state\r\nHost: x'):
            with self.subTest(path=path):self.assertFalse(p.permits('GET',path))
