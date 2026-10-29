"""Public frontend allowlist shared by HTTP serving and source packaging."""
ASSETS = {
    '/': ('index.html', 'text/html; charset=utf-8'),
    '/assets/app.js': ('app.js', 'text/javascript; charset=utf-8'),
    '/assets/style.css': ('style.css', 'text/css; charset=utf-8'),
    '/manifest.webmanifest': ('manifest.webmanifest', 'application/manifest+json; charset=utf-8'),
    '/service-worker.js': ('service-worker.js', 'text/javascript; charset=utf-8'),
    '/assets/icon-192.png': ('icon-192.png', 'image/png'),
    '/assets/icon-512.png': ('icon-512.png', 'image/png'),
}
