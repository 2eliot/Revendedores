
const CACHE_NAME = 'ff-latam-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/freefirelatam',
  '/blockstriker',
  '/static/styles.css',
  '/static/freefirelatam.css',
  '/static/blockstriker.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Devolver desde cache si está disponible
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
