# Les pronostics « exercice par exercice » pour le jour 1 et le jour 2.
#
#   py src/pronostics.py
#
# 1. CALCUL AUTOMATIQUE : pour chaque exercice (1, 2, 3…), le chapitre le plus souvent tombé
#    à cette place depuis la réforme, les années récentes comptant plus (× 0,8 par an).
# 2. CHOIX_MANUELS : les choix éditoriaux d'ExamPredict, qui remplacent le calcul quand ils existent.

import pandas as pd

from moteur import charger

REFORME = 2022
DECROISSANCE = 0.8

# (matière, jour) → {numéro d'exercice: texte affiché}
CHOIX_MANUELS = {
    ("maths", 1): {
        1: "Suites",
        2: "Fonctions (logarithme, convexité)",
        3: "Géométrie dans l'espace",
        4: "Intégrales + équations différentielles",
    },
    ("maths", 2): {
        3: "Suites + équations différentielles",
        4: "Fonctions + intégrales",
    },
    ("physique-chimie", 1): {
        1: "Acide-base (titrage, pH)",
        2: "Chimie organique",
        3: "Mécanique",
    },
    ("physique-chimie", 2): {
        1: "Électricité",
        2: "Mécanique",
        3: "Chimie organique",
    },
    ("svt", 1): {
        1: "Système nerveux et muscles",
        2: "Climat",
    },
}


def calcul_automatique(df, matiere, jour, annee=2027):
    """Liste des chapitres pronostiqués, exercice par exercice (sans répétition)."""
    r = df[(df["matiere"] == matiere) & (df["jour"] == jour) & (df["annee"] >= REFORME)]
    if r.empty:
        return []
    nb_exercices = int(r[r["annee"] == r["annee"].max()]["exercice"].max())
    poids = DECROISSANCE ** (annee - 1 - r["annee"])
    global_jour = poids.groupby(r["famille"]).sum().sort_values(ascending=False)

    pris, resultat = set(), []
    for numero in range(1, nb_exercices + 1):
        place = r["exercice"] == numero
        score = poids[place].groupby(r.loc[place, "famille"]).sum()
        score = (score + 0.01 * global_jour.reindex(score.index)).sort_values(ascending=False)
        restants = [f for f in list(score.index) + list(global_jour.index) if f not in pris]
        choix = restants[0]
        pris.add(choix)
        resultat.append(choix)
    return resultat


def pronostic(df, matiere, jour):
    """Le pronostic final : calcul automatique, puis choix manuels par-dessus.
    Renvoie une liste de (numéro d'exercice, chapitre, origine)."""
    auto = calcul_automatique(df, matiere, jour)
    manuel = CHOIX_MANUELS.get((matiere, jour), {})
    return [(i, manuel.get(i, chap), "choix" if i in manuel else "calcul")
            for i, chap in enumerate(auto, start=1)]


def main():
    df = charger()
    for matiere in ["maths", "physique-chimie", "svt"]:
        for jour in (1, 2):
            print(f"===== {matiere.upper()} · jour {jour} =====")
            for numero, chapitre, origine in pronostic(df, matiere, jour):
                print(f"   Exercice {numero} : {chapitre}   ({origine})")


if __name__ == "__main__":
    main()
