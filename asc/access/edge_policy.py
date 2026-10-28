"""Separate format2 edge binding. Private profile1 is never widened or migrated."""
from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import urlsplit
from .policy import Profile,private_origin
from .access_jwt import access_issuer


def public_origin(value):
    if type(value) is not str:raise ValueError('explicit public HTTPS origin required')
    parsed=urlsplit(value);host=parsed.hostname or ''
    if (parsed.scheme!='https' or value!='https://'+host or len(host)>253 or '.' not in host
            or not all(re.fullmatch('[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',p) for p in host.split('.'))
            or host.rsplit('.',1)[1] in ('local','localhost','lan','internal')):
        raise ValueError('explicit canonical public HTTPS DNS origin required')
    try:ipaddress.ip_address(host)
    except ValueError:return host
    raise ValueError('public origin must be DNS, not an IP')


@dataclass(frozen=True)
class EdgeProfile(Profile):
    listen_origin: str
    access_team: str
    access_audience: str

    @classmethod
    def parse(cls,value):
        fields={'format','mode','frontend_origin','listen_origin','upstream_origin','upstream_pin','upstream_mode',
                'max_body_bytes','access_team','access_audience'}
        if (type(value) is not dict or set(value)!=fields or type(value['format']) is not int
                or value['format']!=2 or value['mode']!='cloudflare-edge'):
            raise ValueError('unsupported explicit edge profile')
        public_origin(value['frontend_origin']);host,_=private_origin(value['listen_origin'])
        if host!='127.0.0.1':raise ValueError('edge origin listener requires exact loopback')
        access_issuer(value['access_team'])
        if type(value['access_audience']) is not str or not re.fullmatch('[0-9a-f]{64}',value['access_audience']):
            raise ValueError('explicit Access audience required')
        Profile.parse({k:value[k] for k in ('upstream_origin','upstream_pin','upstream_mode','max_body_bytes')}|
            {'format':1,'mode':'private-gateway','frontend_origin':value['listen_origin']})
        return cls(**{name:value[name] for name in fields-{'format','mode'}})

    def public(self):
        return {'format':2,'mode':'cloudflare-edge','url':self.frontend_origin,'listen_origin':self.listen_origin,
            'upstream_mode':self.upstream_mode,'access_validation':'RS256 issuer/audience/time +existing ASC owner session',
            'remote_reachability':'UNKNOWN','live_cloudflare_accepted':False,'writer_authority':False,'production_accepted':False}
