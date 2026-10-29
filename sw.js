// Baffus Maximus — service worker (généré par src/build.py depuis src/sw.template.js, ne pas modifier sw.js à la main).
// Met tout le jeu en cache pour jouer hors ligne (les musiques au fil de l'écoute) ; une nouvelle version propose « Mettre à jour ».
const VERSION = 'baffus-1.4.2-235e9d61';
const CORE = [
  './',
  './index.html',
  './en.html',
  './ks-studio.js',
  './ks-back.js',
  './manifest.webmanifest',
  './fonts/lilita-one.woff2',
  './fonts/nunito.woff2',
  './icons/apple-touch-icon.png',
  './icons/favicon.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-512.png',
  './a/adv_agile.webp',
  './a/adv_brute.webp',
  './a/adv_equi.webp',
  './a/adv_rival.webp',
  './a/adv_tank.webp',
  './a/adv_tireur.webp',
  './a/an_banniere.webp',
  './a/an_fans.webp',
  './a/an_lion.webp',
  './a/an_oie.webp',
  './a/an_oie_course.webp',
  './a/arene.webp',
  './a/b_ludus.webp',
  './a/b_table.webp',
  './a/b_temple.webp',
  './a/ch_0.webp',
  './a/ch_1.webp',
  './a/ch_2.webp',
  './a/ch_3.webp',
  './a/ch_4.webp',
  './a/cour.webp',
  './a/esquive.webp',
  './a/fi_charrette.webp',
  './a/fi_poissonnier.webp',
  './a/g_accroupi.webp',
  './a/g_dos.webp',
  './a/g_face.webp',
  './a/g_face_d.webp',
  './a/g_face_g.webp',
  './a/g_fente.webp',
  './a/g_garde.webp',
  './a/g_idle.webp',
  './a/g_joie.webp',
  './a/g_ko.webp',
  './a/g_lancer.webp',
  './a/g_marche.webp',
  './a/g_penche.webp',
  './a/g_poing.webp',
  './a/g_recul.webp',
  './a/g_saut.webp',
  './a/g_sonne.webp',
  './a/g_victoire.webp',
  './a/lg_senateur.webp',
  './a/mur.webp',
  './a/ob_boucliers.webp',
  './a/ob_caisse.webp',
  './a/poisson.webp',
  './a/poisson_ld.webp',
  './a/poisson_lg.webp',
  './a/pt_bavard.webp',
  './a/pt_coquet.webp',
  './a/pt_fanfaron.webp',
  './a/pt_gourm.webp',
  './a/pt_hypo.webp',
  './a/pt_melan.webp',
  './a/pt_opti.webp',
  './a/pt_pares.webp',
  './a/pt_philo.webp',
  './a/pt_poete.webp',
  './a/pt_roman.webp',
  './a/pt_supers.webp',
  './a/ro_couteau_p.webp',
  './a/ro_roue.webp',
  './a/ro_stagiaire.webp',
  './a/route.webp',
  './a/sa_impact.webp',
  './a/sa_jauge.webp',
  './a/sa_sac.webp',
  './a/tf_0.webp',
  './a/tf_1.webp',
  './a/tf_2.webp',
  './a/tf_3.webp',
  './a/tf_4.webp',
  './a/titre.webp',
  './a/tr_bar_face.webp',
  './a/tr_cible.webp',
  './a/tr_mannequin.webp',
  './a/tr_potence.webp',
  './a/tr_tonneau.webp',
  './a/up_autel.webp',
  './a/up_biblio.webp',
  './a/up_cuisine.webp',
  './a/up_salle.webp',
  './a/up_statue.webp',
  './a/up_tribunes.webp'
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
      // pas encore en cache : on laisse passer la requête et on garde le fichier entier pour la prochaine fois
      if (!hit) { e.waitUntil(fetch(url.pathname).then(r => { if (r.ok && r.status === 200) return caches.open(VERSION).then(c => c.put(url.pathname, r)); }).catch(() => {})); return fetch(req); }
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
