# Le moteur de prédiction d'ExamPredict : « quels chapitres vont tomber ? »
#
#   py src/moteur.py                      → toutes les matières
#   py src/moteur.py maths                → une seule matière
#
# 1. compare plusieurs modèles avec un backtest HONNÊTE (années 2022 → 2026 cachées tour à tour)
# 2. garde le meilleur pour chaque matière
# 3. prédit les chapitres 2027, avec un pourcentage et la fiabilité mesurée

import sys
import warnings

import pandas as pd
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

BASE = "data/chapitres_bac.csv"
ANNEES_TEST = [2022, 2023, 2024, 2025, 2026]


def charger(chemin=BASE):
    return pd.read_csv(chemin)


def tombes(df, matiere):
    """Tableau années × chapitres : 1 si le chapitre est tombé cette année-là, 0 sinon."""
    d = df[df["matiere"] == matiere]
    return (pd.crosstab(d["annee"], d["famille"]) > 0).astype(int)


# ---------- Les modèles : chacun renvoie un score par chapitre (plus haut = plus probable) ----------

def modele_frequence(table, annee):
    """Baseline : combien de fois chaque chapitre est tombé, toutes années confondues."""
    return table[table.index < annee].sum()


def modele_vote(table, annee, decroissance=0.8):
    """Vote pondéré : une année récente compte plus qu'une année ancienne."""
    passe = table[table.index < annee]
    poids = pd.Series(decroissance ** (annee - 1 - passe.index), index=passe.index)
    return passe.mul(poids, axis=0).sum()


def modele_logistique(table, annee):
    """Régression logistique : « tombé il y a 1, 2, 3 ans ? » → probabilité de tomber."""
    annees = [a for a in table.index if a < annee]
    lignes, cibles = [], []
    for i in range(3, len(annees)):
        for chap in table.columns:
            lignes.append([table.loc[annees[i - j], chap] for j in (1, 2, 3)])
            cibles.append(table.loc[annees[i], chap])
    if len(set(cibles)) < 2:                     # pas assez de variété pour apprendre
        return modele_vote(table, annee)
    model = LogisticRegression().fit(lignes, cibles)
    futur = [[table.loc[annees[-j], chap] for j in (1, 2, 3)] for chap in table.columns]
    return pd.Series(model.predict_proba(futur)[:, 1], index=table.columns)


MODELES = {
    "fréquence (baseline)": modele_frequence,
    "vote pondéré": modele_vote,
    "régression logistique": modele_logistique,
}


# ---------- L'évaluation honnête ----------

REFORME = 2022   # premier bac du nouveau programme


def candidats(table, annee):
    """Les chapitres « encore au programme » : ceux tombés au moins une fois depuis la réforme,
    AVANT l'année visée (on n'utilise jamais le futur). Avant toute année de réforme : tous."""
    recents = table[(table.index >= REFORME) & (table.index < annee)]
    vus = list(recents.columns[recents.sum() > 0])
    return vus or list(table.columns)


def classer(table, modele, annee):
    """Scores du modèle, limités aux chapitres candidats, du plus probable au moins probable."""
    return modele(table, annee)[candidats(table, annee)].sort_values(ascending=False)


def evaluer(table, modele):
    """Pour chaque année test : on prédit AUTANT de chapitres qu'il en est vraiment tombé (k),
    et on compte combien sont justes. Renvoie (taux du modèle, taux du hasard)."""
    justes = total = hasard = 0
    for annee in ANNEES_TEST:
        if annee not in table.index:
            continue
        reels = set(table.columns[table.loc[annee] == 1])
        k = len(reels)
        prevus = set(classer(table, modele, annee).head(k).index)
        justes += len(prevus & reels)
        total += k
        hasard += k * k / len(candidats(table, annee))   # k chapitres tirés au hasard parmi les candidats
    return justes / total, hasard / total


def predire(df, matiere):
    """Choisit le meilleur modèle au backtest et renvoie un dictionnaire de résultats."""
    table = tombes(df, matiere)
    if table.empty:
        raise ValueError(f"Matière inconnue : {matiere}")
    scores_modeles = {nom: evaluer(table, m) for nom, m in MODELES.items()}
    meilleur = max(scores_modeles, key=lambda nom: scores_modeles[nom][0])
    taux, hasard = scores_modeles[meilleur]

    annee_cible = table.index.max() + 1
    brut = classer(table, MODELES[meilleur], annee_cible)
    pourcentages = (brut / brut.sum() * 100).round(1)
    absents = sorted(set(table.columns) - set(brut.index))
    return {
        "matiere": matiere,
        "annee": int(annee_cible),
        "modele": meilleur,
        "fiabilite": round(taux * 100),
        "hasard": round(hasard * 100),
        "comparaison": {nom: round(t * 100) for nom, (t, h) in scores_modeles.items()},
        "chapitres": pourcentages,
        "absents": absents,
    }


def main():
    df = charger()
    matieres = sys.argv[1:] or sorted(df["matiere"].unique())
    for matiere in matieres:
        try:
            r = predire(df, matiere)
        except ValueError as erreur:
            print(erreur, "· choix possibles :", sorted(df["matiere"].unique()))
            continue
        print(f"===== {matiere.upper()} · prédiction {r['annee']} =====")
        for nom, taux in r["comparaison"].items():
            print(f"   {nom:<24} {taux} % de chapitres trouvés")
        print(f"   {'(hasard)':<24} {r['hasard']} %")
        print(f"→ modèle retenu : {r['modele']} · fiabilité mesurée {r['fiabilite']} %")
        for chap, pct in r["chapitres"].items():
            print(f"   {chap:<32} {pct:5.1f} %")
        print()


if __name__ == "__main__":
    main()
