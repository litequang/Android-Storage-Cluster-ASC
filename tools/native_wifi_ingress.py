"""Private, task-owned QEMU Wi-Fi ingress for qualification only; never runtime IPC.

The SDK console redir targets mynet/10.0.2.15. API35 Wi-Fi uses the distinct
virtio-wifi backend/10.0.2.16. No ADB forwarding, public listener or TLS change.
"""
import os
from pathlib import Path
import re
import socket
import stat


def forward_command(action, port, guest='10.0.2.16'):
    if action not in ('add', 'remove') or type(port) is not int or not 1024 <= port <= 65535 or guest != '10.0.2.16':
        raise ValueError('fixed private Wi-Fi qualification endpoint required')
    return f'hostfwd_{action} virtio-wifi tcp:127.0.0.1:{port}' + (f'-{guest}:9443' if action == 'add' else '')


def has_forward(table, port):
    forward_command('add', port)
    table = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', table)
    section = re.search(r'VLAN -1 \(virtio-wifi\):\r?\n(.*?)(?=VLAN |\Z)', table, re.S)
    return bool(section and re.search(
        rf'^\s*TCP\[HOST_FORWARD\]\s+\d+\s+127\.0\.0\.1\s+{port}\s+10\.0\.2\.16\s+9443\s', section[1], re.M))


def private_socket(path):
    path = Path(path)
    parent = path.parent.stat()
    entry = path.lstat()
    if (parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) != 0o700
            or entry.st_uid != os.getuid() or not stat.S_ISSOCK(entry.st_mode)
            or stat.S_IMODE(entry.st_mode) & 0o077):
        raise ValueError('owned Unix monitor socket and private 0700 parent required')


class OwnedWifiIngress:
    def __init__(self, proc, monitor):
        self.proc, self.monitor = Path(proc), Path(monitor).absolute()
        self.start = (self.proc / 'stat').read_text().split()[21]
        self.port = None
        self.verify()

    def verify(self):
        args = (self.proc / 'cmdline').read_bytes().split(b'\0')
        expected = {b'-avd': b'ASC_NATIVE_CATALOG_API35', b'-port': b'5560',
                    b'-monitor': ('unix:' + str(self.monitor) + ',server,nowait').encode()}
        if (self.proc.stat().st_uid != os.getuid()
                or (self.proc / 'stat').read_text().split()[21] != self.start
                or not Path(os.readlink(self.proc / 'exe')).name.startswith('qemu-system')
                or any(key not in args or args.index(key) + 1 >= len(args)
                       or args[args.index(key) + 1] != value for key, value in expected.items())):
            raise ValueError('live owned API35 QEMU/AVD/port/explicit monitor required')
        private_socket(self.monitor)

    @staticmethod
    def _prompt(connection):
        data = bytearray()
        while b'(qemu)' not in data:
            block = connection.recv(8192)
            if not block or len(data) + len(block) > 65536:
                raise RuntimeError('bounded QEMU response required')
            data.extend(block)
        return data.decode('utf-8', errors='replace')

    def _exchange(self, command):
        self.verify()
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(8)
            connection.connect(str(self.monitor))
            self._prompt(connection)
            connection.sendall(command.encode() + b'\n')
            result = self._prompt(connection)
        self.verify()
        return result

    def add(self, port, guest):
        command = forward_command('add', port, guest)
        if self.port is not None or has_forward(self._exchange('info usernet'), port):
            raise ValueError('never replace an existing forward')
        result = self._exchange(command)
        if any(word in result.lower() for word in ('error', 'failed', 'could not', 'invalid')):
            raise RuntimeError('QEMU refused private Wi-Fi forward')
        self.port = port
        if not has_forward(self._exchange('info usernet'), port):
            raise RuntimeError('actual Wi-Fi forwarding table not confirmed')

    def close(self):
        if self.port is not None:
            port = self.port
            self._exchange(forward_command('remove', port))
            if has_forward(self._exchange('info usernet'), port):
                raise RuntimeError('owned forwarding cleanup not confirmed')
            self.port = None
