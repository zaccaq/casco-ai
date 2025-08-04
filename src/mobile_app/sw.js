// Service Worker per Jarvis Helmet Controller PWA
const CACHE_NAME = 'jarvis-helmet-v1.0.0';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

// Installazione
self.addEventListener('install', function(event) {
  console.log('[SW] Installazione Service Worker...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('[SW] Cache aperta:', CACHE_NAME);
        return cache.addAll(urlsToCache);
      })
      .then(function() {
        console.log('[SW] Service Worker installato');
        return self.skipWaiting();
      })
  );
});

// Attivazione
self.addEventListener('activate', function(event) {
  console.log('[SW] Attivazione Service Worker...');

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Eliminazione cache obsoleta:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      console.log('[SW] Service Worker attivato');
      return self.clients.claim();
    })
  );
});

// Gestione richieste
self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          console.log('[SW] Risposta dalla cache:', event.request.url);
          return response;
        }

        return fetch(event.request).then(function(response) {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(function() {
          console.log('[SW] Offline - servendo dalla cache');
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/index.html');
          }
        });
      })
  );
});

console.log('[SW] Jarvis Helmet Service Worker v1.0.0 caricato');