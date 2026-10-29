// Baffus Maximus — service worker (généré par src/build.py depuis src/sw.template.js, ne pas modifier sw.js à la main).
// Met tout le jeu en cache pour jouer hors ligne ; une nouvelle version propose « Mettre à jour ».
const VERSION = 'baffus-1.4.1-be122bc3';
const CORE = [
  './',
  './index.html',
  './en.html',
  './ks-studio.js',
  './ks-back.js',
  './manifest.webmanifest',
  './a/titre.webp',
  './fonts/lilita-one.woff',
  './fonts/nunito.woff',
  './icons/apple-touch-icon.png',
  './icons/favicon.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-512.png',
  './musique/arene.mp3',
  './musique/defaite.mp3',
  './musique/gazette.mp3',
  './musique/ludus.mp3',
  './musique/minijeux.mp3',
  './musique/titre.mp3',
  './musique/victoire.mp3'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith('baffus-') && k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => { if (e.data === 'skip') self.skipWaiting(); });

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // le manifest passe par le réseau d'abord, pour que l'installation voie la dernière version
  if (url.pathname.endsWith('.webmanifest')) {
    e.respondWith(fetch(req).then(r => { if (r.ok) { const c = r.clone(); caches.open(VERSION).then(x => x.put(req, c)); } return r; }).catch(() => caches.match(req)));
    return;
  }
  // les musiques sont lues par plages (Range) : on découpe la réponse en cache (206) pour Safari comme Chrome
  const range = req.headers.get('range');
  if (range && url.pathname.endsWith('.mp3')) {
    e.respondWith(caches.match(req, { ignoreSearch: true }).then(async hit => {
      if (!hit) return fetch(req);
      const buf = await hit.arrayBuffer(), m = /bytes=(\d*)-(\d*)/.exec(range) || [];
      const start = m[1] ? +m[1] : 0, end = m[2] ? Math.min(+m[2], buf.byteLength - 1) : buf.byteLength - 1;
      return new Response(buf.slice(start, end + 1), { status: 206, headers: {
        'Content-Type': 'audio/mpeg', 'Content-Range': `bytes ${start}-${end}/${buf.byteLength}`, 'Content-Length': String(end - start + 1), 'Accept-Ranges': 'bytes' } });
    }));
    return;
  }
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => hit ||
      fetch(req).then(r => {
        if (r.ok && r.status === 200) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
        return r;
      }).catch(() => req.mode === 'navigate' ? caches.match('./index.html') : undefined)
    )
  );
});
