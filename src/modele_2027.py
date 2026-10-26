import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

tout = pd.read_csv("data/chapitres_bac.csv")


def predire_matiere(matiere):
    df = tout[tout["matiere"] == matiere]
    compte = pd.crosstab(df["annee"], df["famille"])

    annees = list(compte.index)
    lignes = []
    for i in range(3, len(annees)):
        for famille in compte.columns:
            lignes.append({
                "annee": annees[i],
                "avant_1": compte.loc[annees[i - 1], famille],
                "avant_2": compte.loc[annees[i - 2], famille],
                "avant_3": compte.loc[annees[i - 3], famille],
                "y": compte.loc[annees[i], famille],
            })
    data = pd.DataFrame(lignes)

    X = data[["avant_1", "avant_2", "avant_3"]]
    y = data["y"]
    train = data["annee"] < 2024
    test = data["annee"] >= 2024

    model = LinearRegression()
    model.fit(X[train], y[train])
    pred = model.predict(X[test])

    print("=====", matiere.upper(), "=====")
    print("Poids appris :", model.coef_.round(2))
    print("Erreur du modèle :", round(mean_absolute_error(y[test], pred), 2))
    print("Erreur au pif :", round(mean_absolute_error(y[test], [y[train].mean()] * test.sum()), 2))

    model.fit(X, y)
    futur = pd.DataFrame({
        "avant_1": compte.loc[annees[-1]],
        "avant_2": compte.loc[annees[-2]],
        "avant_3": compte.loc[annees[-3]],
    })
    futur["prediction_2027"] = model.predict(futur).round(2)
    print(futur.sort_values("prediction_2027", ascending=False))
    print()


for matiere in ["physique-chimie", "maths", "svt"]:
    predire_matiere(matiere)