"""Owner node insights commands share existing pinned client/hardware guard."""
from .preferences import MODES


def register(parser, handlers, client, cli):
    def execute(args):
        api=client()
        if args.action=='node-insights-enable':
            result=api.request('POST','nodes/enable',{'request_id':args.request_id})
        elif args.action=='node-preference':
            result=api.request('POST','nodes/'+args.node_id+'/preferences',
                               {'request_id':args.request_id,'mode':args.mode})
        else:
            if args.action=='node-scores':path='nodes/scores'
            elif args.action=='node-history':path='nodes/'+args.node_id+'/history?window='+args.window
            else:path='files/'+args.file_id+'/reduction-preview'
            path+=('&' if '?' in path else '?')+'consistency='+args.consistency
            result=api.request('GET',path)
        cli._show(result)
    for name in ('node-insights-enable','node-scores','node-history','node-preference','replica-reduction-preview'):
        a=parser.add_parser(name)
        if name in ('node-history','node-preference'):a.add_argument('node_id')
        if name=='replica-reduction-preview':a.add_argument('file_id')
        if name in ('node-insights-enable','node-preference'):a.add_argument('--request-id',required=True)
        else:a.add_argument('--consistency',choices=('local','strong'),default='local')
        if name=='node-history':a.add_argument('--window',choices=('24h','7d','30d'),default='24h')
        if name=='node-preference':a.add_argument('--mode',choices=MODES,required=True)
        handlers[name]=execute
