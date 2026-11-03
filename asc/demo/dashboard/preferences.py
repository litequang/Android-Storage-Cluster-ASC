"""Optional UI preferences, never cluster identity, storage policy or authority."""
import threading
from ...bridge import private
from ...bridge.contract import Refused
from ...storage.errors import StorageError


class PreferenceError(Exception):
    def __init__(self,status,code):self.status,self.code=status,code


class Preferences:
    def __init__(self,api):
        self.api=api;self.path=api.root/'dashboard/preferences.json';self.lock=threading.Lock()
        self._read()

    def _read(self):
        self.api.pairings._ready()
        cluster=self.api.service.registry.cluster_id()
        try:
            private.directory(self.path.parent)
            try:self.path.lstat()
            except FileNotFoundError:return dict(format=1,cluster_id=cluster,revision=0,display_name=self.api.views.name,refresh_seconds=10)
            value=private.read(self.path)
            if (set(value) != {'format','cluster_id','revision','display_name','refresh_seconds'}
                    or type(value['format']) is not int or value['format']!=1 or value['cluster_id']!=cluster
                    or type(value['revision']) is not int or not 1<=value['revision']<=1000000):raise ValueError()
            self.validate(value['display_name'],value['refresh_seconds'])
            return value
        except (ValueError,TypeError,KeyError,OSError,StorageError,Refused):
            raise PreferenceError(503,'preferences_unavailable') from None

    @staticmethod
    def validate(name,seconds):
        if (type(name) is not str or not name.strip() or len(name)>64 or any(ord(c)<32 for c in name)
                or type(seconds) is not int or not 5<=seconds<=60):raise ValueError('invalid UI preferences')

    def get(self):
        with self.lock:return {'preferences_api_version':1,**self._read()}

    def update(self,obj):
        if (type(obj) is not dict or set(obj)!= {'preferences_api_version','expected_revision','display_name','refresh_seconds'}
                or type(obj['preferences_api_version']) is not int or obj['preferences_api_version']!=1
                or type(obj['expected_revision']) is not int or obj['expected_revision']<0):raise ValueError()
        self.validate(obj['display_name'],obj['refresh_seconds'])
        with self.lock:
            value=self._read()
            if obj['expected_revision']!=value['revision']:raise PreferenceError(409,'preferences_changed')
            if value['revision']>=1000000:raise PreferenceError(409,'preferences_limit')
            value.update(revision=value['revision']+1,display_name=obj['display_name'],refresh_seconds=obj['refresh_seconds'])
            try:private.replace(self.path,value)
            except (OSError,ValueError,StorageError,Refused):raise PreferenceError(503,'preferences_unavailable') from None
            return {'preferences_api_version':1,**value}
