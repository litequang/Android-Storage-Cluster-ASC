"""Controlled existing Demo Node child only; no Controller/Raft/service manager."""
import os
import queue
import threading
from concurrent.futures import Future
from pathlib import Path
import signal
import subprocess
import sys
import time
from ..runtime import running
from ..demo.state import read_json
from ..demo.locks import validate_lock
from .contract import Refused


class OwnedNode:
    def __init__(self, engine):
        self.engine = engine
        self.process = None
        self.commands = queue.Queue(maxsize=8)
        # Linux PDEATHSIG tracks the creating THREAD, not just its process.
        # Spawn from a retained supervisor, never a short-lived IPC handler.
        self.thread = threading.Thread(target=self._loop,name='ASC-owned-node',daemon=True)
        self.thread.start()

    def _loop(self):
        while True:
            operation, result = self.commands.get()
            try:
                value = self._start() if operation=='start' else self._stop()
                result.set_result(value)
            except Exception as exc: result.set_exception(exc)
            if operation=='close':return

    def _request(self, operation):
        result = Future()
        try:self.commands.put_nowait((operation,result))
        except queue.Full:raise Refused('operation_busy') from None
        return result.result(timeout=40)

    def start(self):return self._request('start')
    def stop(self):return self._request('stop')

    def state(self):
        return {'owned': self.process is not None and self.process.poll() is None,
                'state': 'ONLINE' if self.process is not None and self.process.poll() is None else 'OFFLINE',
                'storage_ready': None}

    def _start(self):
        self.engine.check()
        if sys.platform != 'linux': raise Refused('lifecycle_unsupported')
        home = self.engine.root/'node'
        if not (home/'node.json').exists() or not (home/'storage.json').exists():
            raise Refused('node_not_configured')
        if self.process is not None and self.process.poll() is None:
            return {'state':'ALREADY_OWNED','storage_ready':None}
        validate_lock(home/'agent.lock')
        if running(home,'agent') is not False: raise Refused('external_runtime_owned')
        env = dict(os.environ, ASC_HOME=str(home), PYTHONDONTWRITEBYTECODE='1')
        if self.engine.prefix: env['ASC_DEMO_PREFIX'] = self.engine.prefix
        # Fixed launch, no shell/preexec or caller-selected executable/argv/env.
        command = [sys.executable,'-B','-m','asc.bridge.child','--parent',str(os.getpid()),'--state',str(self.engine.root)]
        self.process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[2],env=env,
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline = time.monotonic()+3
        while time.monotonic()<deadline:
            if self.process.poll() is not None: raise Refused('node_start_unconfirmed')
            if running(home,'agent') is True:
                return {'state':'START_REQUESTED','process_observed':True,'storage_ready':None}
            time.sleep(.05)
        return {'state':'START_REQUESTED','process_observed':self.process.poll() is None,'storage_ready':None}

    def _stop(self):
        # Popen.send_signal polls its child before signaling; no PID-file lookup.
        if self.process is None or self.process.poll() is not None:
            return {'state':'NO_OWNED_NODE','external_node_untouched':True}
        self.process.send_signal(signal.SIGINT)
        try:self.process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            self.process.terminate()  # Only this exact still-owned child.
            try:self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:raise Refused('node_stop_unconfirmed') from None
        return {'state':'STOPPED','identity_preserved':True}

    def close(self):
        if self.thread.is_alive():
            self._request('close');self.thread.join(timeout=5)
