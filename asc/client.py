"""HTTPS client using a manually confirmed certificate SHA256 pin."""
import hashlib
import http.client
import json
import ssl
from urllib.parse import urlsplit


class ClientError(Exception):
    def __init__(self, message, status=None, code=None):
        super().__init__(message)
        self.status = status
        self.code = code


def connect_pinned(origin, pin, timeout=12):
    if type(timeout) is not int or not 1 <= timeout <= 900:
        raise ClientError('invalid bounded timeout')
    url = urlsplit(origin)
    if (url.scheme != 'https' or not url.hostname or (url.path not in ('', '/')) or
            url.username or url.password or url.query or url.fragment):
        raise ClientError('origin must be https://HOST:PORT without a path')
    expected = pin.replace(':', '').strip().upper()
    if len(expected) != 64 or any(c not in '0123456789ABCDEF' for c in expected):
        raise ClientError('invalid SHA256 certificate fingerprint')
    # CA validation is intentionally replaced by the out-of-band PIN on private LAN.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    conn = http.client.HTTPSConnection(url.hostname, url.port or 443, timeout=timeout, context=context)
    try:
        conn.connect()
        actual = hashlib.sha256(conn.sock.getpeercert(binary_form=True)).hexdigest().upper()
        if actual != expected:
            raise ClientError('SERVER CERTIFICATE PIN MISMATCH: aborting')
        return conn
    except BaseException:
        conn.close()
        raise


def request_json(origin, pin, method, path, obj=None, token=None, timeout=12):
    conn = connect_pinned(origin, pin, timeout)
    try:
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8') if obj is not None else None
        headers = {'Accept': 'application/json'}
        if data is not None:
            headers['Content-Type'] = 'application/json'
        if token:
            headers['Authorization'] = f'Bearer {token}'
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ClientError('response too large')
        reply = json.loads(raw.decode('utf-8'))
        if not isinstance(reply, dict):
            raise ClientError('invalid server response')
        if response.status >= 400:
            # Only allow known error labels into logs; never reflect arbitrary body text.
            code = reply.get('error')
            allowed = {'unauthorized', 'credential_rejected_repair_required', 'rate_limited',
                       'invalid_or_expired_code', 'bad_request', 'payload_too_large',
                       'not_found', 'registry_unavailable', 'no_eligible_storage',
                       'catalog_unavailable', 'metadata_not_authorized', 'resync_required',
                       'file_not_found', 'job_not_found', 'logical_version_exists', 'idempotency_conflict',
                       'invalid_policy', 'job_state_conflict', 'stale_job_lease', 'verification_required',
                       'protected_or_inactive_node', 'node_not_approved', 'node_credential_changed',
                       'controller_not_ready', 'stale_authority', 'runtime_recovering',
                       'quorum_read_unavailable', 'commit_unconfirmed', 'precondition_conflict',
                       'stale_gc_plan', 'gc_plan_expired', 'stale_gc_proof', 'gc_execution_unconfirmed',
                       'gc_references_held', 'gc_permit_changed', 'gc_permit_rejected', 'physical_gc_locked'}
            code = code if isinstance(code, str) and code in allowed else 'request_failed'
            raise ClientError(f'HTTP {response.status}: {code}', response.status, code)
        return reply
    finally:
        conn.close()
