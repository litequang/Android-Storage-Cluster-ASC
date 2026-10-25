"""Owner-authenticated GET only, before any Runtime mutation/readiness routing."""
from urllib.parse import parse_qs
from ..server import Handler
from .core import observe


def handle(handler,parsed):
    if parsed.path!='/cluster/v1/observability':return False
    if not handler._admin():return True
    if handler.command!='GET':
        Handler._json(handler,403,{'error':'read_only_observer'});return True
    query=parse_qs(parsed.query,strict_parsing=True)
    if (parsed.fragment or set(query)-{'consistency'} or any(len(v)!=1 for v in query.values()) or
            query.get('consistency',['local'])[0] not in ('local','strong')):
        raise ValueError()
    result=observe(handler.server.catalog.runtime,query.get('consistency')==['strong'])
    # Avoid generic Runtime response relabeling; observation owns exact semantics.
    Handler._json(handler,200,result)
    return True
