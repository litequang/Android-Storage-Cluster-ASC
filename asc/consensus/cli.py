"""Explicit stopped development metadata export/import; never generates identities."""
import argparse
import os
from pathlib import Path

from .adapter import import_seed
from .projection import export, validate
from ..catalog.common import canonical
from ..cli import _must_not_protected
from ..probe import inspect
from ..identity import ensure_private_home
from ..store import Registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('export-seed', 'import-seed'))
    parser.add_argument('--registry', required=True)
    parser.add_argument('--seed', required=True)
    args = parser.parse_args()
    if os.name != 'nt' or inspect().get('protected'):
        _must_not_protected('consensus metadata preparation')
    path, seed = Path(args.registry).resolve(), Path(args.seed).resolve()
    if not path.is_file():
        raise ValueError('existing stopped registry required')
    ensure_private_home(seed.parent)
    registry = Registry(path)
    if args.action == 'export-seed':
        with registry.connect() as db:
            if registry.consensus_enabled():
                raise ValueError('seed export requires the pre-consensus stopped registry')
            raw = canonical(validate(export(db)))
        fd = os.open(seed, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    else:
        with seed.open('rb') as stream:
            raw = stream.read(2*1024**2+1)
        import_seed(registry, raw)
    print('Explicit metadata preparation complete; no runtime started.')


if __name__ == '__main__':
    main()
