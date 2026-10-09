#!/usr/bin/env python3
"""Baffus Maximus — fabrique la version en ligne à partir de src/jeu.html.

src/jeu.html est la page unique du jeu (celle de l'artefact, avec le mode test).
Ce script écrit à la racine du dépôt :
  - index.html  : même jeu, avec l'en-tête d'appli (manifest, icônes), les polices locales,
                  le mode hors ligne, et sans le mode test (5 touches sur la version)
  - sw.js       : le service worker, dont le nom de cache change à chaque build
  - a/titre.webp: l'illustration du titre (couverture du hub)

Usage : python3 src/build.py   (depuis la racine du dépôt)
"""
import base64, hashlib, pathlib, re, sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
VERSION_JEU = '1.0'
src = (RACINE / 'src' / 'jeu.html').read_text(encoding='utf-8')


def remplacer(s, avant, apres, n=1):
    if s.count(avant) != n:
        sys.exit(f'build : motif trouvé {s.count(avant)} fois au lieu de {n} : {avant[:80]!r}')
    return s.replace(avant, apres)


# 1) En-tête propre (le haut de src/jeu.html est l'enveloppe de l'artefact)
debut = src.index('<style>\n/* Mise en page')
STYLE_BASE = re.search(r'<style>(:root\{color-scheme:light;box-sizing.*?)</style>', src).group(1)
TETE = f'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Baffus Maximus</title>
<meta name="description" content="Entraîne ton gladiateur avec des mini-jeux, envoie-le dans l'arène et fonde une dynastie de champions. Un jeu de Keismey Studio, jouable dans le navigateur.">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#24101A">
<link rel="icon" href="icons/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Baffus Maximus">
<meta property="og:type" content="website">
<meta property="og:title" content="Baffus Maximus">
<meta property="og:description" content="Du pain, des baffes et une dynastie de gladiateurs. Un jeu de Keismey Studio.">
<meta property="og:image" content="https://keismey.github.io/Baffus-Maximus/icons/icon-512.png">
<link rel="preload" href="fonts/lilita-one.woff" as="font" type="font/woff" crossorigin>
<link rel="preload" href="fonts/nunito.woff" as="font" type="font/woff" crossorigin>
<style>{STYLE_BASE}
@font-face{{font-family:'Lilita One';src:url(fonts/lilita-one.woff) format('woff');font-weight:400;font-style:normal;font-display:swap}}
@font-face{{font-family:'Nunito';src:url(fonts/nunito.woff) format('woff');font-weight:600 900;font-style:normal;font-display:swap}}
</style>
</head><body>
'''
out = TETE + src[debut:]

# 2) Version publique : pas de mode test, numéro de version
out = remplacer(out, "function devPanel(){", "function devPanel(){if(S)S.dev=false;")
out = re.sub(r"let taps=0;\$\('ver'\)\.onclick=\(\)=>\{if\(\+\+taps>=5\)\{taps=0;S\.dev=!S\.dev;sauver\(\);toast\(S\.dev\?'Mode test activé':'Mode test désactivé'\)\}\};", '', out)
if "Mode test activé" in out:
    sys.exit('build : le raccourci du mode test est encore présent')
out = remplacer(out, 'v0.1 · Keismey Studio', f'v{VERSION_JEU} · Keismey Studio')

# 3) Hors ligne + « Nouvelle version disponible »
SW = '''<script>
/* Hors ligne : service worker ; une nouvelle version propose de recharger */
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost')){
  window.addEventListener('load',()=>{
    navigator.serviceWorker.register('sw.js').then(reg=>{
      const propose=w=>{
        if(document.querySelector('.maj'))return;
        const d=document.createElement('div');d.className='toast maj';d.style.cssText='display:flex;gap:10px;align-items:center;pointer-events:auto;z-index:99';
        d.innerHTML='<span>Nouvelle version disponible</span><button class="btn or petit">Mettre à jour</button>';
        d.querySelector('button').onclick=()=>{w.postMessage('skip')};(document.getElementById('app')||document.body).appendChild(d);
      };
      if(reg.waiting&&navigator.serviceWorker.controller)propose(reg.waiting);
      reg.addEventListener('updatefound',()=>{const w=reg.installing;if(!w)return;
        w.addEventListener('statechange',()=>{if(w.state==='installed'&&navigator.serviceWorker.controller)propose(w)})});
    }).catch(()=>{});
    let recharge=false;navigator.serviceWorker.addEventListener('controllerchange',()=>{if(recharge)return;recharge=true;location.reload()});
  });
}
</script>
'''
out = remplacer(out, '</body></html>', SW + '</body></html>')
(RACINE / 'index.html').write_text(out, encoding='utf-8')

# 4) Couverture du hub : l'illustration du titre
m = re.search(r'id="titreBg" alt="" src="data:image/webp;base64,([A-Za-z0-9+/=]+)"', src)
(RACINE / 'a').mkdir(exist_ok=True)
(RACINE / 'a' / 'titre.webp').write_bytes(base64.b64decode(m.group(1)))

# 5) Service worker : nom de cache = empreinte de tout ce qu'il met en cache
fichiers = ['index.html', 'manifest.webmanifest', 'a/titre.webp',
            'fonts/lilita-one.woff', 'fonts/nunito.woff',
            'icons/apple-touch-icon.png', 'icons/favicon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png']
fichiers += sorted('musique/' + p.name for p in (RACINE / 'musique').glob('*.mp3'))
h = hashlib.sha256()
for f in fichiers:
    h.update((RACINE / f).read_bytes())
empreinte = h.hexdigest()[:8]
gabarit = (RACINE / 'src' / 'sw.template.js').read_text(encoding='utf-8')
liste = ',\n'.join(f"  './{f}'" for f in fichiers)
sw = gabarit.replace('__VERSION__', f'baffus-{VERSION_JEU}-{empreinte}').replace('__FICHIERS__', "  './',\n" + liste)
(RACINE / 'sw.js').write_text(sw, encoding='utf-8')
print(f'index.html ({len(out)//1024} Ko), sw.js (cache baffus-{VERSION_JEU}-{empreinte}), a/titre.webp')
