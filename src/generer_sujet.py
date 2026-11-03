# WEEK 3 · DAY 5 · Générer le PDF d'un « sujet probable » à partir des anciens sujets
#
# Usage, depuis la racine du projet :
#   py src/generer_sujet.py data/exams
#
# 1. analyse les PDF du dossier (exercices + thèmes)
# 2. donne un score à chaque thème (fréquent ? récent ?)
# 3. choisit d'anciens exercices qui couvrent les thèmes les plus probables (≈ 20 points)
# 4. fabrique un PDF : une page de garde + les VRAIES pages de ces exercices

import io
import sys
from datetime import date
from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

from pdf_sujets import analyser_dossier, pages_des_exercices

POINTS_VISES = 20


def scorer_themes(sujets):
    """Score de 0 à 1 pour chaque thème : 60 % fréquence + 40 % récence."""
    annees = sorted({s["annee"] for s in sujets})
    derniere = annees[-1]
    vu_en = {}                                   # thème → années où il est tombé
    for s in sujets:
        for ex in s["exercices"]:
            for theme in ex["themes"]:
                vu_en.setdefault(theme, set()).add(s["annee"])
    scores = {}
    for theme, ans in vu_en.items():
        frequence = len(ans) / len(annees)
        recence = 0.5 ** (derniere - max(ans))   # 1 si tombé la dernière année, 0,5 l'année d'avant…
        scores[theme] = round(0.6 * frequence + 0.4 * recence, 2)
    return dict(sorted(scores.items(), key=lambda p: p[1], reverse=True))


def choisir_exercices(sujets, scores):
    """Choisit des exercices dont le thème PRINCIPAL (le premier) n'est pas encore couvert,
    en commençant par les mieux notés, jusqu'à environ 20 points.
    Sans cette règle, on obtiendrait trois exercices de chimie d'affilée."""
    candidats = []
    for s in sujets:
        for ex in s["exercices"]:
            if ex["themes"]:
                note = sum(scores[t] for t in ex["themes"]) / len(ex["themes"])
                candidats.append((note, s["annee"], s, ex))
    candidats.sort(key=lambda c: (c[0], c[1]), reverse=True)

    choisis, couverts, total = [], set(), 0
    for note, annee, s, ex in candidats:
        if total >= POINTS_VISES:
            break
        if ex["themes"][0] not in couverts:      # son thème principal est nouveau
            choisis.append((s, ex, note))
            couverts.update(ex["themes"])
            total += ex["points"]
    return choisis


def propre(texte):
    """Remplace les caractères que la police standard du PDF ne sait pas écrire."""
    for avant, apres in {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                         "…": "...", "œ": "oe", "Œ": "OE", "→": "->"}.items():
        texte = texte.replace(avant, apres)
    return texte.encode("latin-1", "replace").decode("latin-1")


def page_de_garde(sujets, scores, choisis):
    """Fabrique la page de garde et renvoie ses octets PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, propre("ExamPredict AI - Sujet d'entraînement probable"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, propre(f"Généré le {date.today():%d/%m/%Y} à partir de {len(sujets)} sujets : "
                           + ", ".join(str(s['annee']) for s in sujets)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, propre("Thèmes les plus probables"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for theme, score in list(scores.items())[:6]:
        pdf.cell(0, 6, propre(f"- {theme} : score {score:.2f}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, propre("Exercices de ce sujet"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for i, (s, ex, note) in enumerate(choisis, start=1):
        pdf.multi_cell(0, 6, propre(
            f"Exercice {i} ({ex['points']:g} points) - {ex['titre']}\n"
            f"   source : sujet {s['annee']}, exercice {ex['numero']} · thèmes : {', '.join(ex['themes'])}"),
            new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, propre(
        "Avertissement : ce sujet est un entraînement construit à partir des thèmes qui reviennent "
        "dans les anciens sujets. Il ne prédit pas le contenu réel du prochain examen. "
        "Les exercices sont reproduits depuis les sujets officiels fournis par l'utilisateur."))
    return bytes(pdf.output())


def assembler(sujets, scores, choisis, dossier, sortie):
    """Page de garde + vraies pages des exercices choisis → un seul PDF."""
    ecrivain = PdfWriter()
    for page in PdfReader(io.BytesIO(page_de_garde(sujets, scores, choisis))).pages:
        ecrivain.add_page(page)
    for s, ex, note in choisis:
        chemin = Path(dossier) / s["fichier"]
        debut, fin = pages_des_exercices(chemin)[ex["numero"]]
        lecteur = PdfReader(chemin)
        for i in range(debut, fin + 1):
            ecrivain.add_page(lecteur.pages[i])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def main():
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/exams")
    if not dossier.is_dir():
        print(f"Dossier introuvable : {dossier}")
        sys.exit(1)

    sujets = [s for s in analyser_dossier(dossier) if s["exercices"]]
    if len(sujets) < 2:
        print("Il faut au moins 2 sujets PDF lisibles pour repérer des tendances.")
        sys.exit(1)

    scores = scorer_themes(sujets)
    choisis = choisir_exercices(sujets, scores)

    print("📊 Thèmes les plus probables :")
    for theme, score in list(scores.items())[:6]:
        print(f"   {theme:<18} {score:.2f}")
    print("\n📝 Exercices retenus :")
    for s, ex, note in choisis:
        print(f"   {s['annee']} ex {ex['numero']} ({ex['points']:g} pts) {ex['titre']} → {', '.join(ex['themes'])}")

    sortie = Path("data/analyses/sujet_probable.pdf")
    assembler(sujets, scores, choisis, dossier, sortie)
    print(f"\n✅ PDF créé : {sortie}")


if __name__ == "__main__":
    main()
