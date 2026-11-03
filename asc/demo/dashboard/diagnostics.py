"""Owner-only bounded redacted diagnostics using existing canonical observations."""
from ...catalog.common import now
from .. import VERSION
from ..upgrade import diagnose


def report(api):
    api.pairings._ready()
    state=api.views.state();local=diagnose(api.root)
    with api.service.registry.connect() as db:
        jobs={s:db.execute('SELECT COUNT(*) FROM catalog_jobs WHERE state=?',(s,)).fetchone()[0]
              for s in ('PENDING','RUNNING','RETRY','FAILED','COMPLETED')}
    nodes=[]
    fields=('kind','state','quota','reserve','used_bytes','free_bytes','available_bytes','readable','writable','fsync_tested','checked_at')
    for index,node in enumerate(state['nodes']):
        nodes.append(dict(node_number=index+1,online=node['online'],storage_approved=node['storage_approved'],
            probe_error=node['probe_error'],last_seen=node['last_seen'],recorded_replicas=node['recorded_replicas'],
            volumes=[{k:v.get(k) for k in fields} for v in node['volumes']]))
    history=api.history.view()
    return dict(diagnostic_api_version=1,generated_at=now(),source_version=VERSION,mode='single-writer-demo',
        local={k:local.get(k) for k in ('state','role','running')},counts=state['counts'],capacity=state['capacity'],
        capacity_note=state['capacity_note'],nodes=nodes,jobs=jobs,
        history=dict(snapshots=len(history['snapshots']),restores=len(history['restores']),
            verified_snapshots=sum(s['state']=='VERIFIED' for s in history['snapshots'].values()),
            completed_restores=sum(j['state']=='COMPLETED' for j in history['restores'].values())),
        limits=dict(browser_transfer_bytes=api.cfg['max_upload_bytes'],catalog_files=256,snapshots=16,restores=64),
        features=dict(physical_gc=False,automatic_failover=False,raft_runtime=False,recovery_writer=False,
            remote_node_quota_control=False,remote_node_process_control=False),
        scope='Observations only; no writer/quorum proof, raw logs, names, IDs, paths or credentials. Linux synthetic source qualification; physical Android acceptance remains separate.')
