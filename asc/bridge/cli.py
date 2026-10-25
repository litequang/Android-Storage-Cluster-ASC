"""Explicit local bridge; secrets remain private files / hidden input, never argv."""
import argparse
import getpass
import json
from pathlib import Path
import signal
import sqlite3
import threading
from ..storage.errors import StorageError
from .contract import Refused
from .service import provision, Runtime, call


class Parser(argparse.ArgumentParser):
    def error(self,message):self.exit(2,'Invalid bridge command; use --help.\n')


def main():
    parser=Parser(description=__doc__);parser.add_argument('--control',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    setup=commands.add_parser('provision');setup.add_argument('--state',type=Path,required=True)
    setup.add_argument('--allow-join',action='store_true');setup.add_argument('--allow-lifecycle',action='store_true')
    commands.add_parser('run');commands.add_parser('status')
    join=commands.add_parser('quick-join')
    for name in ('controller','pin','cluster-id','name'):join.add_argument('--'+name,required=True)
    join.add_argument('--request-id',required=True);join.add_argument('--resume',action='store_true');join.add_argument('--new-code',action='store_true')
    args=parser.parse_args()
    try:
        if args.command=='provision':
            result=provision(args.control,args.state,['read']+(['join'] if args.allow_join else [])+(['lifecycle'] if args.allow_lifecycle else []))
        elif args.command=='run':
            stop=threading.Event()
            for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
            with Runtime(args.control):stop.wait()
            return 0
        elif args.command=='quick-join':
            params=dict(controller=args.controller,pin=args.pin,cluster_id=args.cluster_id,name=args.name)
            if not args.resume or args.new_code:params['code']=getpass.getpass('One-use node code: ')
            if args.new_code:params['replace_code']=True
            result=call(args.control,'quick_join',params,args.request_id)
        else:result=call(args.control,'status')
        print(json.dumps(result,sort_keys=True));return 0 if result.get('ok',True) else 3
    except (Refused,ValueError,OSError,sqlite3.Error,StorageError):
        print('{"ok":false,"error":"bridge_refused"}');return 3
    except (KeyboardInterrupt,EOFError):return 3


if __name__=='__main__':raise SystemExit(main())
