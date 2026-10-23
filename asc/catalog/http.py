"""Exact /catalog/v1 routes; mutations are owner-admin only, metadata imports are node-scoped."""
import sqlite3
from urllib.parse import urlsplit,parse_qs
from .common import CatalogError
from .. import validation as valid
from ..server import PayloadTooLarge


def handle(handler):
    service=handler.server.catalog
    if service is None:
        return handler._json(404,{'error':'not_found'})
    try:
        parsed=urlsplit(handler.path);parts=parsed.path.removeprefix('/catalog/v1/').split('/')
        query=parse_qs(parsed.query,strict_parsing=True)
        if any(len(v)!=1 for v in query.values()) or parsed.fragment:
            raise ValueError()
        method=handler.command
        node_read=method=='GET' and parts in (['metadata','snapshot'],['metadata','changes'])
        node_ack=method=='POST' and parts==['metadata','ack']
        if node_read:
            allowed={'node_id'} | ({'after'} if parts[-1]=='changes' else set())
            if set(query)!=allowed:raise ValueError()
            node_id=valid.node_id(query['node_id'][0])
            if handler._rate('auth'):return
            if not service.metadata_allowed(node_id,handler._bearer()):
                handler.server.limiter.blocked('auth',handler.client_address[0],consume=True)
                return handler._json(403,{'error':'metadata_not_authorized'})
            value=service.metadata.snapshot() if parts[-1]=='snapshot' else service.metadata.changes(int(query['after'][0]))
            return handler._json(200,value)
        if node_ack:
            if query:raise ValueError()
            if handler._rate('auth'):return
            obj=handler._read_json()
            valid.payload(obj,('node_id','epoch','revision','head_digest'))
            if not service.metadata_allowed(obj['node_id'],handler._bearer()):
                handler.server.limiter.blocked('auth',handler.client_address[0],consume=True)
                return handler._json(403,{'error':'metadata_not_authorized'})
            return handler._json(200,service.metadata_ack(obj))
        if not handler._admin():return
        if method=='GET':
            if parts==['files'] or parts==['jobs']:
                if set(query)-{'offset'}:raise ValueError()
                offset=int(query.get('offset',['0'])[0])
                value=service.catalog.files(offset) if parts==['files'] else service.queue.list(offset)
                return handler._json(200,value)
            if query:raise ValueError()
            if len(parts)==2 and parts[0]=='files':
                return handler._json(200,service.catalog.file(parts[1]))
            if len(parts)==3 and parts[0]=='files' and parts[2]=='replicas':
                entry=service.catalog.file(parts[1])
                return handler._json(200,{k:entry[k] for k in ('replicas','desired_replicas','verified_replicas','available_replicas')})
            if parts in (['metadata','status'],['nodes']):
                return handler._json(200,service.status())
            if len(parts)==2 and parts[0]=='jobs':
                job=service.queue.get(parts[1])
                with service.registry.connect() as db:
                    history=[dict(row) for row in db.execute('SELECT state,error,created_at FROM catalog_job_history WHERE job_id=? ORDER BY sequence DESC LIMIT 200',(job['job_id'],))]
                history.reverse()
                public={k:v for k,v in job.items() if k not in ('run_token','source_generation','target_generation')}
                return handler._json(200,{'job':public,'history':history})
        if method=='POST':
            if query:raise ValueError()
            obj=handler._read_json()
            if parts==['nodes','register']:
                valid.payload(obj,('node_id','device_id'),('origin','pin','volume_ids','metadata_allowed','storage_allowed'))
                return handler._json(200,service.register(obj['node_id'],obj.get('origin'),obj.get('pin'),obj['device_id'],
                    obj.get('volume_ids',[]),obj.get('metadata_allowed',True),obj.get('storage_allowed',True)))
            if parts==['uploads']:
                valid.payload(obj,('idempotency_key','logical_path','size','sha256','policy'),('version',))
                return handler._json(201,service.upload_plan(obj))
            if len(parts)==3 and parts[0]=='uploads' and parts[2]=='complete':
                valid.payload(obj,('session_id','local_file_id'))
                return handler._json(200,service.confirm_upload(parts[1],obj['session_id'],obj['local_file_id']))
            if len(parts)==3 and parts[0]=='files' and parts[2]=='download':
                valid.payload(obj,())
                return handler._json(200,service.download_plan(parts[1]))
            if len(parts)==3 and parts[0]=='files' and parts[2]=='policy':
                valid.payload(obj,('policy',))
                service.refresh()
                service.catalog.mutate('POLICY',{'file_id':parts[1],'policy':obj['policy']})
                service.catalog.schedule(parts[1])
                return handler._json(200,service.catalog.file(parts[1]))
            if parts==['reconcile']:
                valid.payload(obj,())
                return handler._json(200,service.reconcile())
            if parts==['jobs','run']:
                valid.payload(obj,(),('job_id',))
                result=service.run_one(obj.get('job_id'))
                return handler._json(200,{'job':{k:v for k,v in result.items() if k not in ('run_token','source_generation','target_generation')} if result else None})
            if len(parts)==3 and parts[0]=='jobs' and parts[2]=='retry':
                valid.payload(obj,())
                service.queue.retry(parts[1])
                return handler._json(200,{'ok':True})
        return handler._json(404,{'error':'not_found'})
    except CatalogError as exc:
        return handler._json(exc.status,{'error':exc.code})
    except PayloadTooLarge:
        return handler._json(413,{'error':'payload_too_large'})
    except (ValueError,KeyError,TypeError,UnicodeError,RecursionError,OverflowError):
        return handler._json(400,{'error':'bad_request'})
    except sqlite3.Error:
        return handler._json(503,{'error':'catalog_unavailable'})
    except OSError:
        return handler._json(503,{'error':'storage_unavailable'})
