#!/usr/bin/env python3
"""Read-only, owner-local access diagnostics. Never starts or configures a service."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import ssl
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asc.access import gateway
from asc.access.policy import private_origin
from asc.bridge import private
from asc.bridge.contract import decode
from asc.catalog.common import CatalogError
from asc.client import ClientError, request_json
from asc.external.cli import host_guard
from asc.identity import fingerprint_from_pem
from asc.observability.gateway import reject_engine_ancestry
from asc.storage.errors import StorageError


ERRORS = (ValueError, OSError, ClientError, CatalogError, StorageError, http.client.HTTPException)


def mode_matches(value, mode):
    return (type(value) is dict and set(value) == {'mode', 'read_only'}
            and value['mode'] == mode and type(value['read_only']) is bool
            and value['read_only'] == (mode != 'single-writer-demo'))


def listener_get(root, profile, path):
    """Configured private/loopback address only; trusted CA + exact leaf, no redirects."""
    origin = getattr(profile, 'listen_origin', profile.frontend_origin)
    host, port = private_origin(origin)
    context = ssl.create_default_context(cafile=str(root / 'dashboard/ca.crt'))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    connection = http.client.HTTPSConnection(host, port, context=context, timeout=6)
    try:
        connection.connect()
        actual = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
        if actual != fingerprint_from_pem(root / 'dashboard/server.crt').lower():
            raise ValueError('listener identity mismatch')
        connection.request('GET', path, headers={
            'Host': urlsplit(profile.frontend_origin).netloc,
            'Origin': profile.frontend_origin, 'Connection': 'close'})
        response = connection.getresponse()
        lengths = response.headers.get_all('Content-Length', [])
        if (len(response.headers) > 32 or response.headers.get('Transfer-Encoding')
                or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit()
                or int(lengths[0]) > 8192):
            raise ValueError('bounded response required')
        raw = response.read(8193)
        if len(raw) != int(lengths[0]):
            raise ValueError('incomplete response')
        return response.status, decode(raw)
    finally:
        connection.close()


def check(root, *, probe_upstream=False, probe_listener=False):
    """No file/lock/journal creation. All probes are explicit anonymous GETs."""
    checks = dict(profile='UNKNOWN', tls_identity='UNKNOWN',
                  upstream_mode='NOT_REQUESTED', listener_mode='NOT_REQUESTED',
                  anonymous_gate='NOT_REQUESTED')
    result = dict(format=1, scope='operator-local', checks=checks, state='BLOCKED',
                  writer_authority=False, quorum_status='UNKNOWN',
                  remote_reachability='UNKNOWN', vpn_membership='UNKNOWN',
                  authenticated_access='NOT_TESTED', live_deployment_accepted=False)
    try:
        host_guard()
        root = private.directory(root)
        reject_engine_ancestry(root)
        value = private.read(root / 'gateway.json')
        if type(value.get('format')) is int and value['format'] == 2:
            # Optional dependencies are unnecessary for private format1 or offline --help.
            from asc.access.cloudflare import load
        else:
            load = gateway.load
        profile = load(root)
        checks['profile'] = 'VERIFIED'
    except (ImportError, *ERRORS):
        checks['profile'] = 'BLOCKED'
        return result
    try:
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(root / 'dashboard/server.crt', root / 'dashboard/server.key')
        checks['tls_identity'] = 'VERIFIED'
    except ERRORS:
        checks['tls_identity'] = 'BLOCKED'
        return result  # Do not probe a profile whose local identity is untrusted.
    if probe_upstream:
        checks['upstream_mode'] = 'BLOCKED'
        try:
            value = request_json(profile.upstream_origin, profile.upstream_pin,
                                 'GET', '/api/mode', timeout=6)
            if mode_matches(value, profile.upstream_mode):
                checks['upstream_mode'] = 'VERIFIED'
        except ERRORS:
            pass
    if probe_listener:
        edge = hasattr(profile, 'listen_origin')
        checks['listener_mode'] = 'UNKNOWN' if edge else 'BLOCKED'
        checks['anonymous_gate'] = 'BLOCKED'
        try:
            if not edge:
                status, value = listener_get(root, profile, '/api/mode')
                if status == 200 and mode_matches(value, profile.upstream_mode):
                    checks['listener_mode'] = 'VERIFIED'
            status, value = listener_get(root, profile, '/api/state')
            expected = ((403, {'protocol_version': 1, 'error': 'edge_access_denied'})
                        if edge else (401, {'error': 'login_required'}))
            if (status, value) == expected:
                checks['anonymous_gate'] = 'VERIFIED'
        except ERRORS:
            pass
    result['state'] = 'BLOCKED' if 'BLOCKED' in checks.values() else 'CHECKS_PASSED'
    return result


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Invalid access check command; use --help.\n')


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--probe-upstream', action='store_true', help='Pinned GET /api/mode only')
    parser.add_argument('--probe-listener', action='store_true', help='CA-verified anonymous GETs only')
    args = parser.parse_args(argv)
    result = check(args.root, probe_upstream=args.probe_upstream, probe_listener=args.probe_listener)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['state'] == 'CHECKS_PASSED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
