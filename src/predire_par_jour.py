import pandas as pd

tout = pd.read_csv("data/chapitres_bac.csv")
reforme = tout[tout["annee"] >= 2022]
NB_EXOS = {"physique-chimie": 3, "maths": 4, "svt": 2}

for matiere, nb in NB_EXOS.items():
    print("=====", matiere.upper(), "2027 =====")
    for jour in [1, 2]:
        df = reforme[(reforme["matiere"] == matiere) & (reforme["jour"] == jour)]
        compte = pd.crosstab(df["annee"], df["famille"])
        stats = pd.DataFrame({
            "moyenne": compte.mean(),
            "mediane": compte.median(),
            "ecart_type": compte.std(),
        }).sort_values(["moyenne", "ecart_type"], ascending=[False, True])

        print("--- Jour", jour, "(", len(compte), "années ) ---")
        print(stats.round(2))
        for numero, chapitre in enumerate(stats.index[:nb], start=1):
            print("  Exercice", numero, ":", chapitre)
    print()