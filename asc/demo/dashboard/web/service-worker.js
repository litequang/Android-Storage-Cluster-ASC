'use strict';
// Network-only navigation. No API/file interception, CacheStorage, IndexedDB,
// offline writes, background sync, credential storage or Node/process control.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method === 'GET' && event.request.mode === 'navigate' &&
      url.origin === self.location.origin && url.pathname === '/') {
    event.respondWith(fetch(event.request, { cache: 'no-store' }));
  }
});
