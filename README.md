# Baffus Maximus

**Du pain, des baffes et une dynastie de gladiateurs.** Un jeu de Keismey Studio, jouable dans le navigateur et installable sur téléphone.

Entraîne ton gladiateur avec des mini-jeux, envoie-le dans l'arène remporter les cinq ligues, et quand il prend sa retraite, son héritier reprend le flambeau.

Jouer : https://keismey.github.io/Baffus-Maximus/ (aussi dans le hub : https://keismey.github.io/)

Le jeu est en français et en anglais : langue du téléphone au premier lancement, choix dans les Options,
ou `?lang=fr` / `?lang=en` dans l'adresse.

## Fichiers

- `index.html` (français), `en.html` (anglais), `sw.js`, `a/titre.webp` — **générés** par `src/build.py`, ne pas les modifier à la main
- `manifest.webmanifest` — installation sur téléphone
- `musique/` — les musiques du jeu
- `icons/` — icônes de l'appli
- `fonts/` — Lilita One et Nunito (licence SIL OFL, voir `fonts/OFL-*.txt`)
- `src/jeu.html` — le jeu en une seule page (images intégrées), avec le mode test
- `src/en.py` — la traduction anglaise (textes, tournures, valeurs enregistrées dans la sauvegarde)
- `src/i18n.py` — repère les textes du jeu pour la traduction
- `src/sw.template.js` — modèle du service worker

## Mettre à jour le jeu

1. Modifier `src/jeu.html`.
2. Lancer `python3 src/build.py` à la racine du dépôt : ça régénère `index.html`, `en.html` et `sw.js`.
   Le script liste les textes français sans traduction : les ajouter dans `src/en.py`
   (le nom du cache change à chaque build, donc les joueurs voient « Nouvelle version disponible »).
3. Pousser sur `main`. GitHub Pages publie depuis la racine de `main`.

La version en ligne n'a pas de mode test (dans `src/jeu.html`, 5 touches sur le numéro de version de l'écran titre l'activent).

La sauvegarde est dans le `localStorage` du navigateur (clé `dpdb_save_v1`).
