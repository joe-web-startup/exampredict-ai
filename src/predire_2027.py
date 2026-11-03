import pandas as pd

df = pd.read_csv("data/chapitres_bac.csv")


def predire(df, matiere, annee_cible, k=6):
    passe = df[(df["matiere"] == matiere) & (df["annee"] < annee_cible)]
    poids = 0.8 ** (annee_cible - 1 - passe["annee"])
    score = poids.groupby(passe["famille"]).sum()
    return score.sort_values(ascending=False).head(k)


for matiere in sorted(df["matiere"].unique()):
    touches_total = 0
    reels_total = 0
    print("=====", matiere.upper(), "=====")
    for annee in [2022, 2023, 2024, 2025, 2026]:
        prevu = set(predire(df, matiere, annee).index)
        reel = set(df[(df["matiere"] == matiere) & (df["annee"] == annee)]["famille"])
        touches = len(prevu & reel)
        touches_total += touches
        reels_total += len(reel)
        print(annee, ":", touches, "/", len(reel), "chapitres prévus")

    print("Précision :", touches_total, "/", reels_total)

    score = predire(df, matiere, 2027, k=10)
    print((score / score.sum() * 100).round(1))
    print()
