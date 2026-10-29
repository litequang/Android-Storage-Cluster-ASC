"""Optional node-insights state through the existing actual-term quorum CAS."""
import copy
from . import history
from .view import observations
from ..catalog.common import CatalogError, digest, key, now


class Insights:
    def __init__(self, service):
        self.service, self.runtime = service, service.runtime

    def edit(self, action, obj, change, enable=False):
        request=obj.get('request_id')
        if action != 'capture' or request is not None: key(request)
        intent=digest({'action':action,'payload':obj})
        with self.runtime.lock, self.runtime.operation() as view:
            doc=copy.deepcopy(view['document'])
            if 'insights' not in doc:
                if not enable: raise CatalogError('phase3b_not_enabled',409)
                doc['insights']=history.empty()
            state=doc['insights']
            if request in state['requests']:
                previous=state['requests'][request]
                if previous['intent'] != intent: raise CatalogError('request_id_conflict',409)
                return copy.deepcopy(previous['result'])
            result=change(doc,state)
            if request is not None:
                if len(state['requests'])>=128: raise CatalogError('node_request_limit',409)
                state['requests'][request]={'intent':intent,'result':result}
            if doc != view['document']:
                doc['revision']+=1
                self.runtime.commit(view,doc,'nodes-'+digest(request) if request else None,intent)
            return result

    def enable(self, obj):
        return self.edit('enable',obj,lambda d,s:{'enabled':True,'insights_schema':1},enable=True)

    def capture(self):
        if 'insights' not in self.runtime.view()['document']: return
        def change(doc,state):
            stamp=now()
            for node in doc['tables']['nodes']:
                history.record(state,node['node_id'],node['token_version'],observations(doc,node),stamp)
        return self.edit('capture',{},change)

    def preference(self, node_id, obj):
        from .preferences import MODES
        from .. import validation as valid
        valid.node_id(node_id)
        if obj['mode'] not in MODES: raise ValueError('invalid_node_preference')
        def change(doc,state):
            node=next((n for n in doc['tables']['nodes'] if n['node_id']==node_id),None)
            if node is None: raise CatalogError('node_not_found',404)
            row={'mode':obj['mode'],'generation':node['token_version'],'updated_at':now()}
            state.setdefault('preferences',{})[node_id]=row
            return {'node_id':node_id,**row,'automatic_movement':False,'physical_deletions':0}
        return self.edit('preference:'+node_id,obj,change)
