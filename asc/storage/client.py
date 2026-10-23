"""Pinned streaming owner client. Bodies are bounded; downloaded files use exclusive creation."""
import hashlib
import json
from ..client import ClientError, connect_pinned
from .. import validation as valid
from .volumes import CHUNK, identifier


class StorageClient:
    def __init__(self, origin, pin, grant, volume_id, timeout=12):
        valid.secret(grant)
        self.timeout = timeout
        self.origin, self.pin, self.grant = origin, pin, grant
        self.volume_id = identifier(volume_id)

    def _connection(self, method, path, length=None, content_type=None):
        conn = connect_pinned(self.origin, self.pin, self.timeout)
        try:
            conn.putrequest(method, '/storage/v1/' + path)
            conn.putheader('Authorization', 'Bearer ' + self.grant)
            conn.putheader('X-ASC-Volume-ID', self.volume_id)
            conn.putheader('Connection', 'close')
            if length is not None:
                conn.putheader('Content-Length', str(length))
                conn.putheader('Content-Type', content_type)
            conn.endheaders()
            return conn
        except BaseException:
            conn.close()
            raise

    @staticmethod
    def _reply(response):
        raw = response.read(2 * 1024**2 + 1)
        if len(raw) > 2 * 1024**2:
            raise ClientError('response too large')
        reply = json.loads(raw)
        if not isinstance(reply, dict):
            raise ClientError('invalid storage response')
        if response.status >= 400:
            # Do not reflect untrusted server text or secrets into exceptions.
            raise ClientError('storage request rejected', response.status, 'storage_rejected')
        return reply

    def json(self, method, path, obj=None):
        raw = json.dumps(obj).encode() if obj is not None else None
        conn = self._connection(method, path, len(raw) if raw is not None else None, 'application/json')
        try:
            if raw is not None:
                conn.send(raw)
            return self._reply(conn.getresponse())
        finally:
            conn.close()

    def initiate(self, key, logical_path, size, sha256):
        return self.json('POST', 'uploads', {'idempotency_key': key, 'logical_path': logical_path,
                                           'size': size, 'sha256': sha256})['session']

    def upload(self, session_id, source, size):
        identifier(session_id)
        conn = self._connection('PUT', 'uploads/' + session_id, size, 'application/octet-stream')
        try:
            remaining = size
            while remaining:
                chunk = source.read(min(CHUNK, remaining))
                if not chunk:
                    raise ClientError('source ended before declared size')
                conn.send(chunk); remaining -= len(chunk)
            return self._reply(conn.getresponse())['session']
        finally:
            conn.close()

    def commit(self, session_id):
        return self.json('POST', 'uploads/' + identifier(session_id) + '/commit', {})['file']

    def download(self, file_id, output, expected_size, expected_sha256):
        identifier(file_id)
        conn = self._connection('GET', 'files/' + file_id + '/content')
        try:
            response = conn.getresponse()
            if response.status != 200:
                self._reply(response)
                raise ClientError('invalid download status')
            if (response.getheader('Content-Length') != str(expected_size) or
                    response.getheader('X-ASC-SHA256') != expected_sha256):
                raise ClientError('download metadata mismatch')
            count, digest = 0, hashlib.sha256()
            while count < expected_size:
                chunk = response.read(min(CHUNK, expected_size - count))
                if not chunk:
                    raise ClientError('download interrupted')
                output.write(chunk); digest.update(chunk); count += len(chunk)
            if digest.hexdigest() != expected_sha256:
                raise ClientError('download checksum mismatch')
            return {'size': count, 'sha256': digest.hexdigest()}
        finally:
            conn.close()
