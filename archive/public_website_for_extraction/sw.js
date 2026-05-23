// FinPilot Service Worker
// Provides offline support and caching for PWA

const CACHE_NAME = 'finpilot-v1.6.0';
const STATIC_CACHE = 'finpilot-static-v1';
const DYNAMIC_CACHE = 'finpilot-dynamic-v1';
const DATA_CACHE = 'finpilot-data-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/translations.js',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/offline.html',
];

// API patterns that should use network-first strategy
const API_PATTERNS = [
  /\/api\//,
  /yfinance/,
  /polygon\.io/,
  /finnhub\.io/,
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              return name.startsWith('finpilot-') &&
                     name !== STATIC_CACHE &&
                     name !== DYNAMIC_CACHE &&
                     name !== DATA_CACHE;
            })
            .map((name) => {
              console.log('[ServiceWorker] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests with network-first strategy
  if (isApiRequest(url)) {
    event.respondWith(networkFirst(request, DATA_CACHE));
    return;
  }

  // Handle static assets with cache-first strategy
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // Handle other requests with stale-while-revalidate
  event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
});

// Cache strategies

// Cache-first: Use cache, fallback to network
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return offlineFallback();
  }
}

// Network-first: Try network, fallback to cache
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    return offlineFallback();
  }
}

// Stale-while-revalidate: Serve from cache, update in background
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached || offlineFallback());

  return cached || fetchPromise;
}

// Offline fallback page
async function offlineFallback() {
  const cache = await caches.open(STATIC_CACHE);
  const offline = await cache.match('/offline.html');

  if (offline) {
    return offline;
  }

  return new Response(
    '<html><body><h1>Offline</h1><p>Please check your internet connection.</p></body></html>',
    {
      headers: { 'Content-Type': 'text/html' }
    }
  );
}

// Helper functions

function isApiRequest(url) {
  return API_PATTERNS.some((pattern) => pattern.test(url.href));
}

function isStaticAsset(url) {
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2'];
  return staticExtensions.some((ext) => url.pathname.endsWith(ext));
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Sync event:', event.tag);

  if (event.tag === 'sync-watchlist') {
    event.waitUntil(syncWatchlist());
  }

  if (event.tag === 'sync-alerts') {
    event.waitUntil(syncAlerts());
  }
});

async function syncWatchlist() {
  // Sync watchlist changes made offline
  const db = await openDB();
  const pendingChanges = await db.getAll('pending-watchlist');

  for (const change of pendingChanges) {
    try {
      await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(change),
      });
      await db.delete('pending-watchlist', change.id);
    } catch (error) {
      console.error('[ServiceWorker] Sync failed:', error);
    }
  }
}

async function syncAlerts() {
  // Placeholder for alert sync
  console.log('[ServiceWorker] Syncing alerts...');
}

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received');

  let data = { title: 'FinPilot Alert', body: 'New update available' };

  if (event.data) {
    try {
      data = event.data.json();
    } catch (error) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/',
      timestamp: Date.now(),
    },
    actions: [
      { action: 'view', title: 'View' },
      { action: 'dismiss', title: 'Dismiss' },
    ],
    tag: data.tag || 'finpilot-notification',
    renotify: true,
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Focus existing window if open
        for (const client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Periodic sync for background updates
self.addEventListener('periodicsync', (event) => {
  console.log('[ServiceWorker] Periodic sync:', event.tag);

  if (event.tag === 'update-prices') {
    event.waitUntil(updatePricesInBackground());
  }
});

async function updatePricesInBackground() {
  // Fetch latest prices for watchlist symbols
  console.log('[ServiceWorker] Updating prices in background...');

  try {
    const cache = await caches.open(DATA_CACHE);
    const watchlistResponse = await fetch('/api/watchlist');

    if (watchlistResponse.ok) {
      cache.put('/api/watchlist', watchlistResponse.clone());
    }
  } catch (error) {
    console.error('[ServiceWorker] Background update failed:', error);
  }
}

// Simple IndexedDB helper
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('finpilot-sw', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-watchlist')) {
        db.createObjectStore('pending-watchlist', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

console.log('[ServiceWorker] Loaded successfully');
