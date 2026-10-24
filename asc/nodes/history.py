"""Bounded calendar-hour/day aggregates; gaps remain absent/UNKNOWN."""
import math
from . import scoring

METRICS = ('capacity_ratio', 'reachable', 'memory_mb', 'thermal_c')
WINDOWS = {'24h': ('hours', 3600, 24), '7d': ('days', 86400, 7), '30d': ('days', 86400, 30)}


def empty():
    return {'schema': 1, 'history': {}, 'requests': {}}


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid_node_insights')


def validate(state, nodes):
    if (not isinstance(state, dict) or set(state) - {'preferences'} != {'schema', 'history', 'requests'} or
            type(state['schema']) is not int or state['schema'] != 1 or
            not isinstance(state['history'], dict) or len(state['history']) > 16 or
            not isinstance(state['requests'], dict) or len(state['requests']) > 128):
        raise ValueError('invalid_node_insights')
    identities = {n['node_id'] for n in nodes}
    for node_id, history in state['history'].items():
        if node_id not in identities or set(history) != {'generation', 'last_sample_at', 'hours', 'days'}:
            raise ValueError('invalid_node_insights')
        integer(history['generation'], 1, 2**63-1)
        integer(history['last_sample_at'], 0, 2**63-1)
        for field, interval, bound in (('hours',3600,24), ('days',86400,30)):
            rows = history[field]
            if not isinstance(rows,list) or len(rows)>bound:
                raise ValueError('invalid_node_insights')
            previous=(-1,-1)
            for row in rows:
                if set(row) - {'generation'} != {'start','metrics'} or set(row['metrics']) != set(METRICS):
                    raise ValueError('invalid_node_insights')
                integer(row['start'],0,2**63-1)
                generation=row.get('generation',history['generation'])
                integer(generation,1,2**63-1)
                position=(row['start'],generation)
                if row['start'] % interval or not previous < position or row['start'] > history['last_sample_at']:
                    raise ValueError('invalid_node_insights')
                previous=position
                for name, metric in row['metrics'].items():
                    if set(metric) != {'sum','count'}:
                        raise ValueError('invalid_node_insights')
                    integer(metric['count'],0,1440)
                    value=metric['sum']; low,high=(0,1) if name=='reachable' else scoring.RANGES[name]
                    if (type(value) not in (int,float) or not math.isfinite(value) or
                            not low*metric['count'] <= value <= high*metric['count']):
                        raise ValueError('invalid_node_insights')
    for key, receipt in state['requests'].items():
        from ..catalog.common import key as check_key
        check_key(key)
        if (set(receipt) != {'intent','result'} or not isinstance(receipt['intent'],str) or
                len(receipt['intent']) != 64 or not isinstance(receipt['result'],dict)):
            raise ValueError('invalid_node_insights')
    from .preferences import MODES
    preferences=state.get('preferences',{})
    if not isinstance(preferences,dict) or len(preferences)>64:
        raise ValueError('invalid_node_preferences')
    for node_id,row in preferences.items():
        if (node_id not in identities or set(row) != {'mode','generation','updated_at'} or
                row['mode'] not in MODES):
            raise ValueError('invalid_node_preferences')
        integer(row['generation'],1,2**63-1);integer(row['updated_at'],0,2**63-1)
    return state


def record(state, node_id, generation, observations, at):
    """At most one current probe sample/node/hour; no synthesized offline samples."""
    scoring.validate(observations)
    integer(at,0,2**63-1)
    probe=observations['reachable']
    if probe['value'] is None or not 0 <= at-probe['observed_at'] <= scoring.FRESH_SECONDS:
        return
    row=state['history'].get(node_id)
    if row and row['generation'] == generation and at//3600 <= row['last_sample_at']//3600:
        return
    if row is None:
        if len(state['history']) >= 16:
            from ..catalog.common import CatalogError
            raise CatalogError('node_history_limit',409)
        row={'generation':generation, 'last_sample_at':at, 'hours':[], 'days':[]}
        state['history'][node_id]=row
    for field in ('hours','days'):
        for bucket in row[field]:
            bucket.setdefault('generation',row['generation'])
    row['generation']=generation
    row['last_sample_at']=at
    for field,interval,bound in (('hours',3600,24),('days',86400,30)):
        start=at//interval*interval
        row[field]=[r for r in row[field] if start-(bound-1)*interval <= r['start'] <= start]
        bucket=next((r for r in row[field] if r['start']==start and r['generation']==generation),None)
        if bucket is None:
            bucket={'start':start,'generation':generation,'metrics':{n:{'sum':0,'count':0} for n in METRICS}}
            row[field].append(bucket)
        for name in METRICS:
            item=observations[name]
            if item['value'] is not None and 0 <= at-item['observed_at'] <= scoring.FRESH_SECONDS:
                bucket['metrics'][name]['sum']+=int(item['value']) if name=='reachable' else item['value']
                bucket['metrics'][name]['count']+=1
        row[field]=sorted(row[field],key=lambda r:(r['start'],r['generation']))[-bound:]


def summary(state, node_id, window, at, generation=None):
    field,interval,count=WINDOWS[window]
    start=at//interval*interval-(count-1)*interval
    history=state['history'].get(node_id)
    records=[r for r in history[field] if generation is None or r.get('generation',history['generation'])==generation] if history else []
    rows={}
    for row in records:
        target=rows.setdefault(row['start'],{'metrics':{n:{'sum':0,'count':0} for n in METRICS},'generations':[]})
        target['generations'].append(row.get('generation',history['generation']))
        for name in METRICS:
            for field_name in ('sum','count'):
                target['metrics'][name][field_name]+=row['metrics'][name][field_name]
    buckets=[]
    for stamp in range(start,start+interval*count,interval):
        row=rows.get(stamp)
        buckets.append({'start':stamp,'end':min(stamp+interval,at+1), 'generations':row['generations'] if row else [],
            'metrics':{name:{'mean':row['metrics'][name]['sum']/row['metrics'][name]['count']
                      if row and row['metrics'][name]['count'] else None,
                      'samples':row['metrics'][name]['count'] if row else 0,
                      'source':scoring.SOURCES[name]} for name in METRICS}})
    success=sum(r['metrics']['reachable']['sum'] for s,r in rows.items() if start<=s<=at)
    samples=sum(r['metrics']['reachable']['count'] for s,r in rows.items() if start<=s<=at)
    return {'window':window,'alignment':'UTC calendar buckets; current bucket partial',
            'sample_interval_seconds':3600,'generation':history['generation'] if history else None,
            'last_sample_at':history['last_sample_at'] if history else None,
            'reliability':100*success/samples if samples else None,'probe_samples':samples,
            'buckets':buckets,'observed_buckets':sum(any(m['samples'] for m in b['metrics'].values()) for b in buckets),
            'continuous_uptime':None}
