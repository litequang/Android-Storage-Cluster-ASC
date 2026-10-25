"""Explicitly scoped Android Demo Track; Core runtime guards remain unchanged."""
VERSION = '0.4.1-alpha'
CAPABILITIES = ['installer', 'lan-single-writer', 'upgrade-safe', 'dashboard-lite', 'android-volume-anchor']
STATE_FORMATS = {'demo': 1, 'registry': 4, 'manifest': 1, 'metadata': 1, 'config': 1, 'wire': 1}
