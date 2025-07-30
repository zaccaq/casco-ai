// Service Worker per Jarvis Helmet Controller PWA
const CACHE_NAME = 'jarvis-helmet-v1.0.0';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  // Cache delle risorse essenziali
];

// Installazione del Service Worker
self.addEventListener('install', function(event) {
  console.log('🔧 Service Worker: Installazione in corso...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('📦 Cache aperta:', CACHE_NAME);
        return cache.addAll(urlsToCache);
      })
      .then(function() {
        console.log('✅ Service Worker installato con successo');
        return self.skipWaiting();
      })
  );
});

// Attivazione del Service Worker
self.addEventListener('activate', function(event) {
  console.log('🚀 Service Worker: Attivazione in corso...');

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Eliminazione cache obsoleta:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      console.log('✅ Service Worker attivato');
      return self.clients.claim();
    })
  );
});

// Gestione delle richieste (fetch)
self.addEventListener('fetch', function(event) {
  // Solo per richieste GET
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Cache hit - ritorna la risorsa dalla cache
        if (response) {
          console.log('📦 Risposta dalla cache per:', event.request.url);
          return response;
        }

        // Fetch dalla rete
        return fetch(event.request).then(function(response) {
          // Controlla se la risposta è valida
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clona la risposta per la cache
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(function() {
          // Fallback per connessione offline
          console.log('📡 Offline - servendo dalla cache:', event.request.url);

          // Se è una richiesta HTML, ritorna la pagina principale dalla cache
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/index.html');
          }
        });
      })
  );
});

// Gestione messaggi dal client
self.addEventListener('message', function(event) {
  console.log('📨 Messaggio ricevuto dal client:', event.data);

  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;

      case 'GET_VERSION':
        event.ports[0].postMessage({
          type: 'VERSION',
          version: CACHE_NAME
        });
        break;

      case 'CLEAR_CACHE':
        caches.delete(CACHE_NAME).then(() => {
          event.ports[0].postMessage({
            type: 'CACHE_CLEARED',
            success: true
          });
        });
        break;

      default:
        console.log('❓ Tipo messaggio sconosciuto:', event.data.type);
    }
  }
});

// Background Sync (per future implementazioni)
self.addEventListener('sync', function(event) {
  console.log('🔄 Background Sync:', event.tag);

  if (event.tag === 'helmet-command') {
    event.waitUntil(syncHelmetCommands());
  }
});

// Push Notifications (per future implementazioni)
self.addEventListener('push', function(event) {
  console.log('📬 Push ricevuto:', event);

  let notificationData = {};

  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (e) {
      notificationData = {
        title: 'Jarvis Helmet',
        body: event.data.text(),
        icon: '/icon-192.png',
        badge: '/badge-72.png'
      };
    }
  }

  const options = {
    title: notificationData.title || 'Jarvis Helmet',
    body: notificationData.body || 'Notifica dal casco',
    icon: notificationData.icon || '/icon-192.png',
    badge: notificationData.badge || '/badge-72.png',
    tag: 'jarvis-notification',
    data: notificationData.data || {},
    actions: [
      {
        action: 'open',
        title: 'Apri App'
      },
      {
        action: 'dismiss',
        title: 'Ignora'
      }
    ],
    requireInteraction: false,
    silent: false
  };

  event.waitUntil(
    self.registration.showNotification(options.title, options)
  );
});

// Click su notifiche
self.addEventListener('notificationclick', function(event) {
  console.log('🔔 Click su notifica:', event);

  event.notification.close();

  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then(function(clientList) {
        // Se l'app è già aperta, porta in primo piano
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url === '/' && 'focus' in client) {
            return client.focus();
          }
        }

        // Altrimenti apri una nuova finestra
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
    );
  }
});

// Funzioni di utilità
async function syncHelmetCommands() {
  try {
    // Recupera comandi in coda dall'IndexedDB
    const commands = await getQueuedCommands();

    for (const command of commands) {
      try {
        // Tenta di inviare il comando
        const response = await fetch('/api/helmet/command', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(command)
        });

        if (response.ok) {
          await removeQueuedCommand(command.id);
          console.log('✅ Comando sincronizzato:', command.id);
        }
      } catch (error) {
        console.log('❌ Errore sync comando:', error);
      }
    }
  } catch (error) {
    console.log('❌ Errore sync generale:', error);
  }
}

async function getQueuedCommands() {
  // Implementazione IndexedDB per recuperare comandi in coda
  // Per ora ritorna array vuoto
  return [];
}

async function removeQueuedCommand(commandId) {
  // Implementazione IndexedDB per rimuovere comando dalla coda
  console.log('🗑️ Comando rimosso dalla coda:', commandId);
}

// Log versione Service Worker
console.log('🤖 Jarvis Helmet Service Worker v1.0.0 caricato');
console.log('📦 Cache name:', CACHE_NAME);