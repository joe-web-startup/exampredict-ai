# WEEK 3 · DAY 4 · Lire N'IMPORTE QUEL dossier de sujets PDF, sans IA payante
#
# Usage, depuis la racine du projet :
#   py src/pdf_sujets.py data/exams
#
# Pour chaque PDF : le texte, puis les exercices (numéro, titre, points, texte),
# puis les thèmes détectés. Le résultat est enregistré dans data/analyses/sujets.json.

import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from analyzer import CONCEPTS, count_keyword

logging.getLogger("pypdf").setLevel(logging.ERROR)   # cache les avertissements de police de pypdf

# « Exercice 2 - Datation d'une roche (6 points) »  →  numéro, titre, points
MOTIF_TITRE = re.compile(r"exercice\s+(\d+)\s*[-–:]?\s*([^\n(]*)\((\d+(?:[.,]\d+)?)\s*points?\)", re.IGNORECASE)
MOTIF_ANNEE = re.compile(r"(19|20)\d{2}")


def extraire_texte(chemin):
    """Renvoie tout le texte d'un PDF (chaîne vide si le PDF est illisible)."""
    try:
        lecteur = PdfReader(chemin)
        return "\n".join(page.extract_text() or "" for page in lecteur.pages)
    except Exception as erreur:
        print(f"PDF ignoré : {Path(chemin).name} ({erreur})")
        return ""


def decouper_exercices(texte):
    """Découpe le texte d'un sujet en exercices.
    Renvoie une liste de dictionnaires : numero, titre, points, texte."""
    titres = list(MOTIF_TITRE.finditer(texte))
    exercices = []
    for i, titre in enumerate(titres):
        debut = titre.start()
        fin = titres[i + 1].start() if i + 1 < len(titres) else len(texte)
        exercices.append({
            "numero": int(titre.group(1)),
            "titre": titre.group(2).strip(" -–"),
            "points": float(titre.group(3).replace(",", ".")),
            "texte": texte[debut:fin].strip(),
        })
    return exercices


def detecter_themes(texte, dictionnaire=CONCEPTS, minimum=3, maximum=3):
    """Renvoie les thèmes principaux d'un exercice.
    Score d'un thème = nombre total d'apparitions de ses mots-clés (en mots entiers).
    Un seul « pression » ou « volume » ne suffit pas : il faut au moins `minimum`
    apparitions, et on garde les `maximum` thèmes les plus forts."""
    texte = texte.lower()
    scores = {theme: sum(count_keyword(texte, mot) for mot in mots)
              for theme, mots in dictionnaire.items()}
    forts = sorted((theme for theme, n in scores.items() if n >= minimum),
                   key=lambda theme: scores[theme], reverse=True)
    return forts[:maximum]


def analyser_dossier(dossier):
    """Analyse tous les PDF d'un dossier. Renvoie la liste des sujets."""
    sujets = []
    for chemin in sorted(Path(dossier).glob("*.pdf")):
        texte = extraire_texte(chemin)
        annee = MOTIF_ANNEE.search(chemin.name)
        exercices = decouper_exercices(texte)
        for ex in exercices:
            ex["themes"] = detecter_themes(ex["texte"])
        sujets.append({
            "fichier": chemin.name,
            "annee": int(annee.group(0)) if annee else 0,
            "exercices": exercices,
        })
    return sujets


def main():
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/exams")
    if not dossier.is_dir():
        print(f"Dossier introuvable : {dossier}")
        sys.exit(1)

    sujets = analyser_dossier(dossier)
    if not sujets:
        print(f"Aucun PDF dans {dossier}")
        sys.exit(1)

    frequence = Counter()
    for sujet in sujets:
        print(f"\n📄 {sujet['fichier']} ({sujet['annee']})")
        if not sujet["exercices"]:
            print("   ⚠️ aucun exercice reconnu (format de titre différent ?)")
        for ex in sujet["exercices"]:
            print(f"   Ex {ex['numero']} ({ex['points']:g} pts) {ex['titre']}")
            print(f"      thèmes : {', '.join(ex['themes']) or 'aucun reconnu'}")
            frequence.update(ex["themes"])

    print(f"\n📊 Thèmes les plus fréquents sur {len(sujets)} sujets :")
    for theme, n in frequence.most_common(8):
        print(f"   {theme:<18} {n} exercice(s)")

    sortie = Path("data/analyses/sujets.json")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(sujets, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAnalyse enregistrée dans {sortie}")


if __name__ == "__main__":
    main()
