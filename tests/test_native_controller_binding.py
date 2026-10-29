"""Actual existing Core TLS transport from native adapter, no enrollment/authority."""
import contextlib
import json
from pathlib import Path
import secrets
import ssl
import sqlite3
import tempfile
import threading
import unittest
import uuid
from asc.identity import make_cert,fingerprint_from_pem
from asc.server import Server
from asc.store import Registry
from tests import test_native_engine_adapter as library

class NativeControllerBindingTests(unittest.TestCase):
    def test_real_tls_pin_cluster_outage_reconnect_without_enrollment(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cluster=str(uuid.uuid4());reg=Registry(root/'registry.sqlite3');reg.initialize(cluster)
            make_cert(root/'cert',root/'key');pin=fingerprint_from_pem(root/'cert').lower();admin=secrets.token_urlsafe(32)
            ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(root/'cert',root/'key')
            port=0
            for cycle in range(2):
                server=Server(('127.0.0.1',port),reg,admin);port=server.server_address[1];server.tls_context=ctx
                origin='https://127.0.0.1:'+str(port);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    proof=json.loads(library.adapter.inspect_controller(origin,pin,cluster))
                    self.assertEqual(proof['state'],'TLS_AND_CLUSTER_MATCH');self.assertFalse(proof['enrollment_performed']);self.assertFalse(proof['writer_authority'])
                    for wrong_pin,wrong_cluster in [('0'*64,cluster),(pin,str(uuid.uuid4()))]:
                        self.assertEqual(json.loads(library.adapter.inspect_controller(origin,wrong_pin,wrong_cluster))['state'],'UNKNOWN')
                finally:server.shutdown();server.server_close();thread.join()
                self.assertEqual(json.loads(library.adapter.inspect_controller(origin,pin,cluster))['state'],'UNKNOWN')
            with contextlib.closing(sqlite3.connect(root/'registry.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM enrollments').fetchone()[0],0)
