"""Host qualification guards; not Android TLS/Node acceptance."""
import os
from pathlib import Path
import socket
import tempfile
import unittest

from tools.native_wifi_ingress import OwnedWifiIngress, forward_command, has_forward, private_socket


class NativeWifiIngressTests(unittest.TestCase):
    def test_forward_scope_cannot_expand_or_inject_commands(self):
        self.assertEqual(forward_command('add', 32000),
                         'hostfwd_add virtio-wifi tcp:127.0.0.1:32000-10.0.2.16:9443')
        self.assertEqual(forward_command('remove', 32000),
                         'hostfwd_remove virtio-wifi tcp:127.0.0.1:32000')
        for value in (True, 0, 80, 65536, '32000\nquit'):
            with self.subTest(port=value):
                with self.assertRaises(ValueError):forward_command('add', value)
        for guest in ('10.0.2.15', '0.0.0.0', '10.0.2.16\nquit', '::1'):
            with self.subTest(guest=guest):
                with self.assertRaises(ValueError):forward_command('add', 32000, guest)
        with self.assertRaises(ValueError):forward_command('quit', 32000)

    def test_actual_forward_must_match_wifi_backend_and_entire_endpoint(self):
        row='  TCP[HOST_FORWARD] 176       127.0.0.1 32000       10.0.2.16 9443     0     0\n'
        table='VLAN -1 (mynet):\nVLAN -1 (virtio-wifi):\n'+row+'(qemu) '
        self.assertTrue(has_forward(table, 32000))
        for wrong in (table.replace('(virtio-wifi)', '(mynet)'), table.replace('127.0.0.1', '0.0.0.0'),
                      table.replace('10.0.2.16', '10.0.2.15'), table.replace('9443', '9444'),
                      'VLAN -1 (mynet):\n'+row+'VLAN -1 (virtio-wifi):\n(qemu) '):
            with self.subTest(table=wrong):self.assertFalse(has_forward(wrong, 32000))
        self.assertFalse(has_forward(table, 32001))

    def test_real_unix_socket_permissions_and_symlink_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);root.chmod(0o700);path=root/'monitor.sock'
            with socket.socket(socket.AF_UNIX) as monitor:
                monitor.bind(str(path));path.chmod(0o600)
                private_socket(path)
                alias=root/'alias';alias.symlink_to(path)
                with self.assertRaises(ValueError):private_socket(alias)
                path.chmod(0o660)
                with self.assertRaises(ValueError):private_socket(path)
                path.chmod(0o600);root.chmod(0o755)
                with self.assertRaises(ValueError):private_socket(path)
                root.chmod(0o700)

    def test_regular_file_and_non_qemu_process_refuse_before_monitor_io(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);root.chmod(0o700);path=root/'monitor.sock';path.write_bytes(b'not a socket');path.chmod(0o600)
            with self.assertRaises(ValueError):private_socket(path)
            with self.assertRaises(ValueError):OwnedWifiIngress(Path('/proc')/str(os.getpid()), path)

    def test_truncated_monitor_reply_is_not_confirmation(self):
        left,right=socket.socketpair()
        with left,right:
            left.sendall(b'no final prompt');left.shutdown(socket.SHUT_WR)
            with self.assertRaises(RuntimeError):OwnedWifiIngress._prompt(right)

    def test_oversized_monitor_reply_is_bounded(self):
        left,right=socket.socketpair()
        with left,right:
            left.sendall(b'x'*65537);left.shutdown(socket.SHUT_WR)
            with self.assertRaises(RuntimeError):OwnedWifiIngress._prompt(right)
