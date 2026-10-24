"""ASC Demo entry point: bounded explicit commands, no implicit Core runtime fallback."""
import argparse
import json
from pathlib import Path
import sys
from .installer import install, preflight


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight', help='read-only device/dependency/volume discovery')
    setup = commands.add_parser('install', help='verify and install immutable source only')
    setup.add_argument('--prefix', type=Path, default=Path.home() / '.local/share/asc-demo')
    setup.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'preflight':
            result = preflight()
            print(json.dumps(result, indent=2))
            return 0 if result['allowed'] else 3
        result = install(Path(__file__).resolve().parents[2], args.prefix, args.dry_run)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        # Never dump arbitrary dependency exceptions, paths or private configuration.
        print('ASC Demo refused: preflight, package, state or path validation failed. Preserve state; see DEMO-QUICKSTART.', file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
