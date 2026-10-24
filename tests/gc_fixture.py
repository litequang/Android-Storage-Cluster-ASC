"""Test subprocess launcher only. No product CLI/config/env activates GC."""
import os
from types import SimpleNamespace
from unittest.mock import patch


def main():
    import asc.failover.cli as cli
    from asc.failover.service import Service, RuntimeHandler
    from asc.storage.runtime import StorageRuntime
    from asc.storage.http import StorageHandler
    from asc.replication.arena import fixture_controller_context
    from asc.replication.sandbox import fixture_executor

    class SyntheticService(Service):
        def __init__(self,runtime,*args,**kwargs):
            super().__init__(runtime,*args,**kwargs)
            self.gc_test_context=fixture_controller_context(runtime.path.parent)

    class SyntheticHandler(RuntimeHandler):
        def _runtime_dispatch(self):
            if self.command=='POST' and self.path in ('/fixture/gc/issue','/fixture/gc/age'):
                import copy
                from asc.catalog.common import CatalogError,identifier
                from asc import validation as valid
                try:
                    if not self._admin():return
                    obj=self._read_json();service=self.server.catalog
                    if self.path.endswith('/issue'):
                        valid.payload(obj,('gc_job_id',))
                        raw,exact,target=service.gc.issue(obj['gc_job_id'])
                        return self._json(200,{'raw':raw,'exact':exact,'target':target})
                    valid.payload(obj,('file_id',));identifier(obj['file_id'])
                    # Share the actual Controller Runtime lock. This fixture-only
                    # ordinary append is not a second writer on the same sidecar.
                    with service.runtime.lock,service.runtime.operation() as view:
                        doc=copy.deepcopy(view['document'])
                        def age(reg,catalog):
                            for i in range(1024):catalog.mutate('POLICY',{'file_id':obj['file_id'],
                                'policy':'replicated_2' if i%2==0 else 'single'})
                        service.replication.workspace(doc,age);doc['revision']+=1
                        service.runtime.commit(view,doc)
                    return self._json(200,{'appended':1024})
                except CatalogError as exc:return self._json(exc.status,{'error':exc.code})
            return super()._runtime_dispatch()
        do_GET=do_POST=_runtime_dispatch

    class SyntheticStorage(StorageRuntime):
        def __enter__(self):
            result=super().__enter__()
            class LostGCReply(StorageHandler):
                def _json(handler,status,data):
                    marker=self.engine.home/'test-gc-lost-ack'
                    if status==200 and handler.path.startswith('/storage/v1/gc/') and marker.exists():
                        marker.unlink();handler.close_connection=True
                        return  # Actual journal/unlink completed; only the TLS reply is lost.
                    return super()._json(status,data)
            self.server.RequestHandlerClass=LostGCReply
            if os.name=='posix':
                # Fresh arena binding before the harness uploads any fake body.
                for volume in self.engine.volumes.records():
                    executor=fixture_executor(self.engine,volume['volume_id'])
                    self.server.gc_executors[volume['volume_id']]=executor
            return result

    with patch.object(cli,'Service',SyntheticService),patch.object(cli,'StorageRuntime',SyntheticStorage),patch.object(cli,'RuntimeHandler',SyntheticHandler):
        with patch.object(cli,'os',SimpleNamespace(name='nt')),patch.object(cli,'inspect',return_value={
                'protected':False,'installation_allowed':True,'simulation':True}):
            cli.main()


if __name__=='__main__':main()
