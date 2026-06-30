const CACHE_NAME = 'amr-cache-v1';
const urlsToCache = ['/', '/index.html', '/manifest.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache)));
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET, extensions, and API calls
  if (event.request.method !== 'GET') return;
  if (url.protocol === 'chrome-extension:') return;
  if (url.pathname.startsWith('/api') ||
      url.pathname.includes('/alerts') ||
      url.pathname.includes('/predict') ||
      url.pathname.includes('/analytics') ||
      url.pathname.includes('/export')) {
    return; // Let the browser handle it directly
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
