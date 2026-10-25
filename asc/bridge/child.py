"""Fixed Linux parent-death fence before exec of the existing guarded Demo node."""
import argparse
import ctypes
import os
from pathlib import Path
import signal
import sys
from ..demo.installer import guard
from ..demo.state import inspect_state


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--parent',type=int,required=True)
    parser.add_argument('--state',type=Path,required=True);args=parser.parse_args()
    # Set in this single-threaded child, never a preexec hook in a threaded server.
    if sys.platform!='linux' or os.getppid()!=args.parent:return 197
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(1,signal.SIGTERM,0,0,0)!=0 or os.getppid()!=args.parent:return 197  # PR_SET_PDEATHSIG
    guard();inspect_state(args.state)
    command=[sys.executable,'-B','-m','asc.demo.cli','--state',str(args.state),'run-node']
    os.execve(sys.executable,command,dict(os.environ,ASC_HOME=str(args.state/'node')))


if __name__=='__main__':raise SystemExit(main())
