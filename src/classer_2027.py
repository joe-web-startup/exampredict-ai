# WEEK 3 · DAY 3 · Classification : « ce chapitre va-t-il tomber ? » OUI ou NON
# Lance depuis la racine du projet :  py src/classer_2027.py
import sys
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

tout = pd.read_csv("data/chapitres_bac.csv")
matiere = sys.argv[1] if len(sys.argv) > 1 else "physique-chimie"
seuil = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

df = tout[tout["matiere"] == matiere]
if df.empty:
    print("Matière inconnue. Choix possibles :", sorted(tout["matiere"].unique()))
    sys.exit(1)
print("=====", matiere.upper(), "· seuil", seuil, "=====")
# 1. Pour chaque année et chaque chapitre : 1 s'il est tombé, 0 sinon
tombe = (pd.crosstab(df["annee"], df["famille"]) > 0).astype(int)
annees = list(tombe.index)

# 2. Les features : est-il tombé il y a 1, 2, 3 ans ?  La cible y : tombe-t-il cette année ?
lignes = []
for i in range(3, len(annees)):
    for chapitre in tombe.columns:
        lignes.append({
            "annee": annees[i],
            "chapitre": chapitre,
            "avant_1": tombe.loc[annees[i - 1], chapitre],
            "avant_2": tombe.loc[annees[i - 2], chapitre],
            "avant_3": tombe.loc[annees[i - 3], chapitre],
            "y": tombe.loc[annees[i], chapitre],
        })
data = pd.DataFrame(lignes)
X = data[["avant_1", "avant_2", "avant_3"]]
y = data["y"]

# 3. Couper DANS LE TEMPS : on apprend sur le passé, on teste sur les dernières années
train = data["annee"] < 2024
test = data["annee"] >= 2024

model = LogisticRegression()
model.fit(X[train], y[train])
pred = model.predict(X[test])

print("Accuracy   :", round(accuracy_score(y[test], pred), 2))
print("Precision  :", round(precision_score(y[test], pred, zero_division=0), 2))
print("Recall     :", round(recall_score(y[test], pred, zero_division=0), 2))
print("Matrice de confusion (lignes = vrai 0/1, colonnes = prédit 0/1) :")
print(confusion_matrix(y[test], pred))

# 4. La baseline : toujours répondre la classe la plus fréquente
majoritaire = y[train].mode()[0]
print("Accuracy au pif (toujours", majoritaire, ") :", round(accuracy_score(y[test], [majoritaire] * test.sum()), 2))

# 5. Probabilités 2027
model.fit(X, y)
futur = pd.DataFrame({
    "avant_1": tombe.loc[annees[-1]],
    "avant_2": tombe.loc[annees[-2]],
    "avant_3": tombe.loc[annees[-3]],
})
futur["proba_2027"] = model.predict_proba(futur[["avant_1", "avant_2", "avant_3"]])[:, 1].round(2)
print(futur.sort_values("proba_2027", ascending=False).head(6))
