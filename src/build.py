#!/usr/bin/env python3
"""Baffus Maximus — fabrique la version en ligne à partir de src/jeu.html.

src/jeu.html est le jeu en une seule page, en français, avec le mode test.
Ce script écrit à la racine du dépôt :
  - index.html  : le jeu en français
  - en.html     : le jeu en anglais (traduction : src/en.py, repérage des textes : src/i18n.py)
  - sw.js       : le service worker, dont le nom de cache change à chaque build
  - a/titre.webp: l'illustration du titre (couverture du hub)
Les deux pages ont l'en-tête d'appli (manifest, icônes), les polices locales, le mode hors ligne,
et pas de mode test (5 touches sur la version).

  python3 src/build.py              (depuis la racine du dépôt)
  python3 src/build.py --artifact D  écrit aussi D/index.html et D/en.html : les deux pages AVEC le mode test,
                                     pour l'aperçu (sans manifest ni service worker)
"""
import base64, hashlib, json, pathlib, re, sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / 'src'))
import i18n, en as EN

VERSION_JEU = '1.3'
SRC = (RACINE / 'src' / 'jeu.html').read_text(encoding='utf-8')

# Suivi Cloudflare Web Analytics (version publiée uniquement, pas l'aperçu de test)
CF_ANALYTICS = """<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "cdb82226cd1b401d9e4f4e899f9b8425"}'></script><!-- End Cloudflare Web Analytics -->"""


def remplacer(s, avant, apres, n=1):
    if s.count(avant) != n:
        sys.exit(f'build : motif trouvé {s.count(avant)} fois au lieu de {n} : {avant[:90]!r}')
    return s.replace(avant, apres)


# ---------- Traduction anglaise ----------
def tableau(src, nom):
    m = re.search(r'const ' + nom + r'=\[(.*?)\];', src, re.S)
    return re.findall(r"'((?:[^'\\]|\\.)*)'", m.group(1))


def table_sauvegarde():
    """Valeurs enregistrées dans la sauvegarde : français → anglais."""
    t = {}
    for nom in EN.LISTES:
        for v in tableau(SRC, nom):
            if v in EN.TRAD and EN.TRAD[v] != v:
                t[v] = EN.TRAD[v]
    for v in EN.RAISONS:
        if v in EN.TRAD and EN.TRAD[v] != v:
            t[v] = EN.TRAD[v]
    return t


def anglais(page):
    for avant, apres in EN.PATCH:
        if avant not in page:
            sys.exit(f'build (en) : PATCH introuvable : {avant[:90]!r}')
        page = page.replace(avant, apres)
    page, utilises, _ = i18n.appliquer(page, EN.TRAD, EN.CONTEXTE)
    inutiles = [k for k in EN.TRAD if k not in utilises]
    # finitions typographiques
    page = page.replace('« ', '“').replace(' »', '”')
    page = re.sub(r'(\$\{[^{}]*\}|\d) %', r'\1%', page)
    page = re.sub(r'(\}|</b>) : ', r'\1: ', page)
    page = remplacer(page, "const LANG='fr';", "const LANG='en';")
    # textes français qui restent (contrôle)
    restes = sorted({t for _, _, t in i18n.textes(page)
                     if re.search(r'[éèêàçùâîôûœ]|\b(le|la|les|une?|des|du|et|est|pour|avec)\b', t)
                     and not t.startswith(('data:', 'px ', 'italic'))})
    return page, inutiles, restes


def avec_trd(page, table):
    return remplacer(page, 'const TRD={};', 'const TRD=' + json.dumps(table, ensure_ascii=False) + ';')


# ---------- En-tête et options de publication ----------
STYLE_BASE = re.search(r'<style>(:root\{color-scheme:light;box-sizing.*?)</style>', SRC).group(1)
DESCR = {
    'fr': ("Entraîne ton gladiateur avec des mini-jeux, envoie-le dans l'arène et fonde une dynastie de champions. Un jeu de Keismey Studio, jouable dans le navigateur.",
           "Du pain, des baffes et une dynastie de gladiateurs. Un jeu de Keismey Studio."),
    'en': ("Train your gladiator with mini-games, send him into the arena and found a dynasty of champions. A Keismey Studio game you can play in your browser.",
           "Bread, slaps and a dynasty of gladiators. A Keismey Studio game."),
}
# Langue : ?lang=fr|en la fixe ; sinon le dernier choix (Options) ; sinon la langue du téléphone.
LANGUE_JS = {
    'fr': "(function(){try{var k='baffus_lang',q=new URLSearchParams(location.search).get('lang'),s=localStorage.getItem(k);"
          "if(q==='fr'||q==='en'){localStorage.setItem(k,q);s=q}"
          "var l=s||(/^fr/i.test((navigator.languages&&navigator.languages[0])||navigator.language||'fr')?'fr':'en');"
          "if(l==='en')location.replace('en.html')}catch(e){}})();",
    'en': "(function(){try{var k='baffus_lang',q=new URLSearchParams(location.search).get('lang'),s=localStorage.getItem(k);"
          "if(q==='fr'||q==='en'){localStorage.setItem(k,q);s=q}"
          "if(s==='fr')location.replace('index.html')}catch(e){}})();",
}


def tete(lang, appli):
    d, og = DESCR[lang]
    pwa = f'''<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#24101A">
<link rel="icon" href="icons/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Baffus Maximus">
<link rel="alternate" hreflang="fr" href="https://keismey.github.io/Baffus-Maximus/?lang=fr">
<link rel="alternate" hreflang="en" href="https://keismey.github.io/Baffus-Maximus/en.html?lang=en">
<link rel="preload" href="fonts/lilita-one.woff" as="font" type="font/woff" crossorigin>
<link rel="preload" href="fonts/nunito.woff" as="font" type="font/woff" crossorigin>
''' if appli else ''
    polices = ('''@font-face{font-family:'Lilita One';src:url(fonts/lilita-one.woff) format('woff');font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'Nunito';src:url(fonts/nunito.woff) format('woff');font-weight:600 900;font-style:normal;font-display:swap}''' if appli else '')
    gfonts = '' if appli else '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lilita+One&family=Nunito:wght@600;700;800;900&display=swap">\n'
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script>{LANGUE_JS[lang]}</script>
{'<script src="ks-back.js"></script>' if appli else ''}
<title>Baffus Maximus</title>
<meta name="description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Keismey Studio">
<meta property="og:title" content="Baffus Maximus">
<meta property="og:description" content="{og}">
<meta property="og:url" content="https://keismey.github.io/Baffus-Maximus/">
<meta property="og:image" content="https://keismey.github.io/Baffus-Maximus/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Baffus Maximus · Keismey Studio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Baffus Maximus">
<meta name="twitter:description" content="{og}">
<meta name="twitter:image" content="https://keismey.github.io/Baffus-Maximus/og.jpg">
{pwa}{gfonts}<style>{STYLE_BASE}
{polices}
</style>
</head><body>
'''


SW_JS = '''<script>
/* Hors ligne : service worker ; une nouvelle version propose de recharger */
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost')){
  window.addEventListener('load',()=>{
    navigator.serviceWorker.register('sw.js').then(reg=>{
      const propose=w=>{
        if(document.querySelector('.maj'))return;
        const d=document.createElement('div');d.className='toast maj';d.style.cssText='display:flex;gap:10px;align-items:center;pointer-events:auto;z-index:99';
        d.innerHTML='<span>__NOUVELLE__</span><button class="btn or petit">__MAJ__</button>';
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
MAJ_TXT = {'fr': ('Nouvelle version disponible', 'Mettre à jour'), 'en': ('New version available', 'Update')}


def page(lang, appli):
    debut = SRC.index('<style>\n/* Mise en page')
    corps = SRC[debut:]
    if lang == 'en':
        corps, inutiles, restes = anglais(corps)
        corps = avec_trd(corps, table_sauvegarde())
    else:
        inutiles, restes = [], []
        corps = avec_trd(corps, {v: k for k, v in table_sauvegarde().items()})
    out = tete(lang, appli) + corps
    out = remplacer(out, 'v0.1 · Keismey Studio', f'v{VERSION_JEU} · Keismey Studio')
    if appli:
        out = remplacer(out, "function devPanel(){", "function devPanel(){if(S)S.dev=false;")
        out = re.sub(r"let taps=0;\$\('ver'\)\.onclick=\(\)=>\{if\(\+\+taps>=5\)\{taps=0;S\.dev=!S\.dev;sauver\(\);toast\(S\.dev\?'[^']*':'[^']*'\)\}\};", '', out)
        if 'S.dev=!S.dev' in out:
            sys.exit('build : le raccourci du mode test est encore présent')
        n, m = MAJ_TXT[lang]
        out = remplacer(out, '</body></html>', SW_JS.replace('__NOUVELLE__', n).replace('__MAJ__', m) + CF_ANALYTICS + '\n</body></html>')
    return out, inutiles, restes


# ---------- Écriture ----------
fr, _, _ = page('fr', True)
en, inutiles, restes = page('en', True)
(RACINE / 'index.html').write_text(fr, encoding='utf-8')
(RACINE / 'en.html').write_text(en, encoding='utf-8')

m = re.search(r'id="titreBg" alt="" src="data:image/webp;base64,([A-Za-z0-9+/=]+)"', SRC)
(RACINE / 'a').mkdir(exist_ok=True)
(RACINE / 'a' / 'titre.webp').write_bytes(base64.b64decode(m.group(1)))

fichiers = ['index.html', 'en.html', 'ks-back.js', 'manifest.webmanifest', 'a/titre.webp',
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
print(f'index.html ({len(fr)//1024} Ko), en.html ({len(en)//1024} Ko), sw.js (cache baffus-{VERSION_JEU}-{empreinte}), a/titre.webp')

if inutiles:
    print(f'\n{len(inutiles)} clé(s) de traduction jamais utilisées :')
    for k in inutiles:
        print('  ·', k)
if restes:
    print(f'\n{len(restes)} texte(s) peut-être encore en français dans en.html :')
    for t in restes:
        print('  ·', t)

if '--artifact' in sys.argv:
    dest = pathlib.Path(sys.argv[sys.argv.index('--artifact') + 1])
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'index.html').write_text(page('fr', False)[0], encoding='utf-8')
    (dest / 'en.html').write_text(page('en', False)[0], encoding='utf-8')
    print(f'\nAperçu (avec mode test) : {dest}/index.html, {dest}/en.html')
