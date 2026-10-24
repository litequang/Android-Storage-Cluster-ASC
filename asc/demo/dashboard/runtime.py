"""Optional HTTPS listener shares the Controller's lifecycle, Catalog and authority."""
from pathlib import Path
import ssl
import threading
from ...server import Server
from ..state import read_json
from .http import DashboardAPI, DashboardHandler
from .tls import load_config


class DashboardRuntime:
    def __init__(self, root, marker, service, client):
        self.root, self.marker, self.service, self.client = Path(root), marker, service, client

    def __enter__(self):
        cfg = load_config(self.root, self.marker)
        name = read_json(self.root / 'controller/controller.json')['node_name']
        self.api = DashboardAPI(self.root, cfg, self.service, self.client, name)
        self.server = Server((cfg['host'], cfg['port']), None, '', handler=DashboardHandler)
        self.server.api = self.api
        self.server.slots = threading.BoundedSemaphore(8)
        self.server.daemon_threads = False
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(self.root / 'dashboard/server.crt', self.root / 'dashboard/server.key')
            self.server.tls_context = context
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return self
        except BaseException:
            self.server.server_close()
            self.api.close()
            raise

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.api.close()
