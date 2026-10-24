"""Explicitly scoped Android Demo Track; Core runtime guards remain unchanged."""
VERSION = '0.3.0-alpha'
CAPABILITIES = ['installer', 'lan-single-writer', 'upgrade-safe']
STATE_FORMATS = {'demo': 1, 'registry': 4, 'manifest': 1, 'metadata': 1, 'config': 1, 'wire': 1}
