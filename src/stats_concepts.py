import pandas as pd
from document_loader import load_documents
from analyzer import find_concepts
documents = load_documents("data/exams")
lignes = {}
for nom, texte in documents.items():
    lignes[nom[:4]] = find_concepts(texte)
df = pd.DataFrame(lignes).T.fillna(0)
print(df)
pd.set_option("display.max_columns", None)
stats = pd.DataFrame({
    "moyenne": df.mean(),
    "mediane": df.median(),
    "ecart_type": df.std(),
})
print(stats.round(1))
print(df.corr().round(2))
df.to_csv("data/concepts_par_examen.csv")
print("Matrice sauvegardée ✅")