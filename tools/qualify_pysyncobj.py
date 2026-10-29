"""Qualify one pinned upstream artifact; never imports ASC or starts listeners.

Exit 0: all sampled gates passed (not full Raft acceptance).
Exit 1: engine rejected by a sampled safety gate.
Exit 2: artifact/download/probe error; qualification is inconclusive.
No package installation, setup.py execution or retained third-party source.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import urllib.request
from unittest.mock import patch

VERSION = "0.3.17"
SHA256 = "8aaef68141714d556173778a51bcc4e221b6fd4c971dc1240f3ab4c0d2dfe765"
MAX_ARCHIVE = 1024 * 1024


def artifact(args):
    if args.archive:
        with Path(args.archive).open("rb") as stream:
            data = stream.read(MAX_ARCHIVE + 1)
    else:
        url = "https://pypi.org/pypi/pysyncobj/" + VERSION + "/json"
        with urllib.request.urlopen(url, timeout=20) as response:
            metadata = json.loads(response.read(MAX_ARCHIVE))
        source = next(item for item in metadata["urls"]
                      if item["packagetype"] == "sdist" and item["digests"]["sha256"] == SHA256)
        url = source["url"]
        if not url.startswith("https://files.pythonhosted.org/"):
            raise ValueError("unexpected artifact host")
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read(MAX_ARCHIVE + 1)
    if len(data) > MAX_ARCHIVE or hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("artifact size/checksum rejected")
    return data


def unpack_package(data, root):
    # Copy only immediate package Python modules. Never execute a packaging script,
    # extract paths supplied by tar, follow links, or retain a dependency in ASC.
    prefix = "pysyncobj-" + VERSION + "/pysyncobj/"
    seen = set()
    package = root / "pysyncobj"
    package.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.name.startswith(prefix):
                continue
            name = member.name[len(prefix):]
            if "/" in name or "\\" in name or not name.endswith(".py"):
                continue
            if not member.isfile() or member.size > MAX_ARCHIVE or name in seen:
                raise ValueError("unexpected package member")
            seen.add(name)
            with archive.extractfile(member) as stream:
                (package / name).write_bytes(stream.read(MAX_ARCHIVE + 1))
    if "__init__.py" not in seen:
        raise ValueError("missing package")


def qualify(root):
    from pysyncobj import SyncObj, SyncObjConf
    from pysyncobj.journal import FileJournal
    from pysyncobj.node import TCPNode
    from pysyncobj.transport import Transport, TCPTransport

    checks = []

    def record(name, passed, evidence):
        checks.append({"gate": name, "pass": bool(passed), "evidence": evidence})

    # Direct transport callbacks are used solely for deterministic qualification.
    # There are no sockets, clocks, threads or simulated successful quorum here.
    class CaptureTransport(Transport):
        def __init__(self, obj, own, peers):
            super().__init__(obj, own, peers)
            self.sent = []

        def send(self, node, message):
            self.sent.append((node.id, dict(message)))
            return True

    own = "127.0.0.1:19001"
    first = "127.0.0.1:19002"
    second = "127.0.0.1:19003"

    def seed(name):
        path = str(root / name)
        journal = FileJournal(path)
        try:
            journal.add(b"\x01", 1, 7)  # upstream NO_OP, index 1, term 7
            journal.setCurrentTerm(7, first)
        finally:
            journal._destroy()
        return path

    path = seed("clean.journal")
    journal = FileJournal(path)
    try:
        got = (journal.getCurrentTerm(), journal.getVotedForNodeId())
        record("clean_restart_retains_term_vote", got == (7, first),
               {"term": got[0], "vote_retained": got[1] == first})
    finally:
        journal._destroy()

    for damage in ("missing", "corrupt"):
        path = seed(damage + ".journal")
        meta = Path(path + ".meta")
        if damage == "missing":
            meta.unlink()
        else:
            meta.write_bytes(b"not-a-valid-pickle")
        node = None
        try:
            node = SyncObj(own, [first, second],
                           conf=SyncObjConf(autoTick=False, useFork=False,
                                            journalFile=path, pollerType="select"),
                           transportClass=CaptureTransport)
            transport = node._SyncObj__transport
            transport._onMessageReceived(TCPNode(second),
                                         {"type": "request_vote", "term": 7,
                                          "last_log_index": 1, "last_log_term": 7})
            voted_again = any(peer == second and msg.get("type") == "response_vote"
                              and msg.get("term") == 7 for peer, msg in transport.sent)
            record(damage + "_meta_refuses_participation", False,
                   {"startup_refused": False, "second_vote_same_term": voted_again})
        finally:
            if node is not None:
                node.destroy()

    journal = FileJournal(str(root / "durable.journal"))
    try:
        import os
        with patch.object(os, "fsync", wraps=os.fsync) as fsync:
            journal.setCurrentTerm(8, first)
            record("term_vote_calls_fsync_before_return", fsync.call_count > 0,
                   {"fsync_calls": fsync.call_count,
                    "scope": "observes calls; not a physical power-cut test"})
        mapped = journal._FileJournal__journalFile
        with patch.object(mapped, "flush", wraps=mapped.flush) as flush:
            journal.add(b"\x01", 1, 8)
            record("log_append_flushes_mapping_before_return", flush.call_count > 0,
                   {"mmap_flush_calls": flush.call_count,
                    "scope": "journal.add boundary; no power-loss claim"})
    finally:
        journal._destroy()

    # Exercise the actual default incoming handshake with a fake connection,
    # claiming a configured peer address, without presenting any credential.
    class Connection:
        def __init__(self):
            self.disconnected = False

        def disconnect(self):
            self.disconnected = True

        def setOnMessageReceivedCallback(self, callback):
            self.callback = callback

    from types import SimpleNamespace
    transport = TCPTransport.__new__(TCPTransport)
    Transport.__init__(transport, None, None, [])
    peer = TCPNode(first)
    connection = Connection()
    transport._syncObj = SimpleNamespace(encryptor=None)
    transport._nodeAddrToNode = {first: peer}
    transport._unknownConnections = {connection}
    transport._connections = {}
    transport._onIncomingMessageReceived(connection, first)
    accepted = transport._connections.get(peer) is connection
    record("default_transport_authenticates_peer_identity", not accepted,
           {"address_claim_accepted_without_credential": accepted,
            "scope": "default password=None; custom pinned transport not implemented"})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--archive", help="local official pysyncobj-0.3.17.tar.gz")
    group.add_argument("--download", action="store_true",
                       help="fetch pinned artifact over verified HTTPS; no install")
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    try:
        data = artifact(args)
        with tempfile.TemporaryDirectory(prefix="asc-engine-probe-") as directory:
            root = Path(directory)
            unpack_package(data, root)
            if any(name == "pysyncobj" or name.startswith("pysyncobj.")
                   for name in sys.modules):
                raise ValueError("probe requires fresh Python process")
            sys.path.insert(0, directory)
            try:
                checks = qualify(root)
            finally:
                sys.path.remove(directory)
                for name in list(sys.modules):
                    if name == "pysyncobj" or name.startswith("pysyncobj."):
                        del sys.modules[name]
        accepted = all(item["pass"] for item in checks)
        print(json.dumps({"engine": "pysyncobj", "version": VERSION,
                          "sha256": SHA256, "qualified": accepted,
                          "checks": checks}, indent=2))
        return 0 if accepted else 1
    except Exception as exc:
        # Fixed diagnostic: never emit a local path, URL credentials or payload.
        print(json.dumps({"qualified": None, "error": "qualification_inconclusive",
                          "exception_type": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
