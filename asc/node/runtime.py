"""Owned Node session: existing StorageHandler/Engine and Core heartbeat.

Platform factory supplies the TLS listener; no second HTTP backend, Catalog,
shell, auto enrollment/approval, voter, GC executor or Controller promotion.
"""
import threading
import time
from .. import validation
from ..agent import heartbeat
from ..client import ClientError
from ..storage.http import StorageServer
from ..storage.runtime import validate_host
from .socket import NativeSocket
from .storage import NativeStorage


class NativeRuntime:
    def __init__(self, context, factory, profile):
        self.context, self.factory, self.profile = context, factory, dict(profile)
        validation.profile(self.profile)
        if self.profile.get('protected') is not False:
            raise ValueError('device_not_qualified')
        self.closed = False
        self.stop_event = threading.Event()
        self.listener = self.server = self.engine = self.opened = None
        self.threads = []
        self.controller = 'UNKNOWN'; self.error = None; self.last_heartbeat = None
        self.storage = None

    def start(self, host, port):
        validate_host(host)
        if type(port) is not int or not 0 <= port <= 65535 or self.opened is not None or self.closed:
            raise ValueError('invalid_node_start')
        # Port0 is reserved for synthetic/in-process qualification. Native factory
        # separately validates its private address/device/API and bounded sockets.
        self.node = self.context.load()['node']
        if self.node is None:
            raise ValueError('enrollment_required')
        try:
            self.opened = NativeStorage(self.context).open()
            self.engine = self.opened.__enter__()
            self.storage = self.engine.capabilities()
            self.listener = self.factory.open(self.context.tls_context(), host, port)
            self.bound_port = self.listener.port()
            # No Python listener is bound. Native JSSE TLS streams enter the SAME
            # original request slots/handler and Controller grant introspection.
            self.server = StorageServer(('127.0.0.1', 0), self.engine, self.node, bind_and_activate=False)
            self.server.daemon_threads = False
            for name, action in (('asc-owned-node-tls', self._serve), ('asc-owned-node-agent', self._agent)):
                thread = threading.Thread(target=action, name=name, daemon=True)
                self.threads.append(thread); thread.start()
            return self.status()
        except BaseException:
            self.close()
            raise

    def _serve(self):
        try:
            while not self.stop_event.is_set():
                connection = self.listener.accept()
                if connection is not None:
                    request = NativeSocket(connection)
                    self.server.process_request(request, request.getpeername())
        except Exception:
            if not self.stop_event.is_set():
                self.error = 'listener_unavailable'; self.stop_event.set()

    def _agent(self):
        while not self.stop_event.is_set():
            try:
                self.storage = self.engine.capabilities()
                heartbeat(self.node, dict(self.profile, storage=self.storage))
                self.controller = 'ONLINE'; self.last_heartbeat = int(time.time()); self.error = None
            except ClientError as exc:
                self.controller = 'OFFLINE'; self.error = 'controller_unavailable'
                if exc.status in (401, 403):
                    self.error = 'credential_rejected'; self.stop_event.set(); self.listener.close()
            except Exception:
                self.controller = 'UNKNOWN'; self.error = 'heartbeat_unavailable'
            self.stop_event.wait(10)

    def status(self):
        node = self.context.load()['node']
        return {'state': 'STOPPED' if self.closed else 'STOPPING' if self.stop_event.is_set() else 'RUNNING',
                'node_id': node['node_id'] if node else None, 'cluster_id': node['cluster_id'] if node else None,
                'port': self.bound_port if self.listener is not None and not self.closed else None,
                'controller': self.controller, 'last_heartbeat': self.last_heartbeat, 'error': self.error,
                'storage': self.storage, 'storage_approved': None, 'failure_domain_approved': None,
                'writer_authority': False, 'raft': False, 'physical_gc': False}

    def close(self):
        if self.closed:
            return
        self.stop_event.set()
        if self.listener is not None:
            self.listener.close()
        for thread in self.threads:
            if thread is not threading.current_thread():
                thread.join(15)
                if thread.is_alive():
                    raise RuntimeError('node_stop_pending')
        if self.server is not None:
            self.server.server_close()
        if self.engine is not None:
            self.opened.__exit__(None, None, None)
        self.closed = True
