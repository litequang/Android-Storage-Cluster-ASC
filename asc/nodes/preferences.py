"""Owner allocation preferences; never auto-moves or deletes replicas."""
MODES = ('auto','preferred','avoid-new-storage','drain','protected')
BLOCK_NEW = {'avoid-new-storage','drain','protected'}


def effective(state, node_id, generation):
    row=state.get('preferences',{}).get(node_id)
    if row is None: return 'auto'
    # Restrictive preferences survive re-pair; stale preferred never promotes a new identity.
    if row['generation'] != generation and row['mode'] not in BLOCK_NEW:
        return 'auto'
    return row['mode']
