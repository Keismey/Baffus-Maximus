"""Baffus Maximus — repérage des textes du jeu, pour la traduction.

textes(page) renvoie la liste des morceaux de texte visibles de src/jeu.html, avec leur position :
  - le texte du balisage HTML (hors <script> et <style>) et ses attributs aria-label / title / alt,
  - dans le script : le contenu des chaînes '…' et "…", et les morceaux de texte des gabarits `…`
    (hors ${…}), découpés autour des balises HTML qu'ils contiennent.
Chaque morceau est (debut, fin, texte) ; le texte est sans les espaces de bord.
Le code lui-même (noms de variables, clés…) n'est jamais touché : on ne remplace que ces morceaux.
"""
import re

ATTR = re.compile(r'(?:aria-label|title|alt|placeholder)="([^"]*)"')


def _morceaux_html(s, base, out):
    """Découpe un bout de HTML en nœuds texte + attributs lisibles."""
    k = 0
    for m in re.finditer(r'<[^>]*>', s):
        _ajoute(s, k, m.start(), base, out)
        for a in ATTR.finditer(m.group(0)):
            _ajoute(s, m.start() + a.start(1), m.start() + a.end(1), base, out)
        k = m.end()
    _ajoute(s, k, len(s), base, out)


def _ajoute(s, a, b, base, out):
    seg = s[a:b]
    st = seg.strip()
    if not st or not re.search(r'[A-Za-zÀ-ÿ]', st):
        return
    a2 = a + (len(seg) - len(seg.lstrip()))
    out.append((base + a2, base + a2 + len(st), st))


def _scan_script(js, base, out):
    n = len(js)
    k = 0
    prev = ''  # dernier caractère significatif (pour distinguer / division et /regex/)

    def gabarit(k):
        """k pointe juste après le ` ouvrant ; renvoie la position après le ` fermant."""
        debut = k
        while k < n:
            c = js[k]
            if c == '\\':
                k += 2
                continue
            if c == '`':
                _morceaux_html(js[debut:k], base + debut, out)
                return k + 1
            if c == '$' and k + 1 < n and js[k + 1] == '{':
                _morceaux_html(js[debut:k], base + debut, out)
                k = expression(k + 2)
                debut = k
                continue
            k += 1
        return k

    def expression(k):
        """Parcourt ${ … } (code), avec chaînes et gabarits imbriqués ; renvoie la position après }."""
        prof = 1
        p = '('
        while k < n:
            c = js[k]
            if c in '\'"':
                k = chaine(k)
                p = 'a'
                continue
            if c == '`':
                k = gabarit(k + 1)
                p = 'a'
                continue
            if c == '/' and p in '(,=:[!&|?{};+-*%<>~^' and js[k + 1] not in '/*':
                k = regex(k)
                p = 'a'
                continue
            if c == '{':
                prof += 1
            elif c == '}':
                prof -= 1
                if prof == 0:
                    return k + 1
            if not c.isspace():
                p = c
            k += 1
        return k

    def chaine(k):
        q = js[k]
        e = k + 1
        while e < n and js[e] != q:
            if js[e] == '\\':
                e += 1
            e += 1
        contenu = js[k + 1:e]
        if '<' in contenu and '>' in contenu:
            _morceaux_html(contenu, base + k + 1, out)
        else:
            _ajoute(contenu, 0, len(contenu), base + k + 1, out)
        return e + 1

    def regex(k):
        e = k + 1
        classe = False
        while e < n:
            c = js[e]
            if c == '\\':
                e += 2
                continue
            if c == '[':
                classe = True
            elif c == ']':
                classe = False
            elif c == '/' and not classe:
                break
            e += 1
        e += 1
        while e < n and js[e].isalpha():
            e += 1
        return e

    while k < n:
        c = js[k]
        if js.startswith('//', k):
            k = js.find('\n', k)
            if k < 0:
                break
            continue
        if js.startswith('/*', k):
            k = js.find('*/', k) + 2
            continue
        if c in '\'"':
            k = chaine(k)
            prev = 'a'
            continue
        if c == '`':
            k = gabarit(k + 1)
            prev = 'a'
            continue
        if c == '/' and (prev in '(,=:[!&|?{};+-*%<>~^' or prev == ''):
            k = regex(k)
            prev = 'a'
            continue
        if not c.isspace():
            prev = c if not (c.isalnum() or c in '_$') else 'a'
            # mots-clés après lesquels un / ouvre une regex
            if c.isalpha():
                m = re.match(r'[A-Za-z_$][\w$]*', js[k:])
                if m.group(0) in ('return', 'typeof', 'case', 'of', 'in'):
                    prev = '('
                k += len(m.group(0))
                continue
        k += 1


def textes(page):
    """Tous les morceaux de texte de la page, triés par position."""
    out = []
    # Le CSS et les URI de données ne contiennent pas de texte à traduire
    zones = []
    for m in re.finditer(r'<script>(.*?)</script>', page, re.S):
        zones.append(('js', m.start(1), m.end(1)))
    pos = 0
    for typ, a, b in sorted(zones, key=lambda z: z[1]):
        html = page[pos:a]
        html = re.sub(r'<style>.*?</style>', lambda m: ' ' * len(m.group(0)), html, flags=re.S)
        html = re.sub(r'data:[a-z]+/[a-z0-9+.-]+;base64,[A-Za-z0-9+/=]+', lambda m: ' ' * len(m.group(0)), html)
        _morceaux_html(html, pos, out)
        _scan_script(page[a:b], a, out)
        pos = b
    reste = re.sub(r'<style>.*?</style>', lambda m: ' ' * len(m.group(0)), page[pos:], flags=re.S)
    _morceaux_html(reste, pos, out)
    out = [t for t in out if not t[2].startswith('data:')]
    return sorted(set(out))


def appliquer(page, trad, contexte=None):
    """Remplace chaque morceau dont le texte est une clé de `trad`.
    `contexte` : liste de (texte, avant, traduction) pour les cas où le même texte se traduit
    différemment selon ce qui le précède (on compare les 40 caractères avant le morceau)."""
    morceaux = textes(page)
    utilises = set()
    res = []
    k = 0
    for a, b, t in morceaux:
        rempl = None
        if contexte:
            for (tx, avant, tr) in contexte:
                if tx == t and avant in page[max(0, a - 60):a]:
                    rempl = tr
                    utilises.add(('ctx', tx, avant))
                    break
        if rempl is None and t in trad:
            rempl = trad[t]
            utilises.add(t)
        if rempl is not None:
            debut = a
            # ponctuation anglaise : pas d'espace avant « : ! ? ; » ni avant l'apostrophe du génitif
            if rempl[:1] in ':!?;’' and page[a - 1:a] == ' ':
                debut = a - 1
            res.append(page[k:debut])
            res.append(rempl)
            k = b
    res.append(page[k:])
    return ''.join(res), utilises, morceaux
