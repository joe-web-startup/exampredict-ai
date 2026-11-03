# Le site web d'ExamPredict AI (Streamlit)
#
# Lancer en local, depuis la racine du projet :
#   py -m streamlit run src/app.py

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from generer_sujet import generer
from moteur import charger, predire

st.set_page_config(page_title="ExamPredict AI", page_icon="📄")
st.title("📄 ExamPredict AI")

onglet_chapitres, onglet_sujet = st.tabs(["🎯 Chapitres probables", "📝 Sujet d'entraînement (PDF)"])

# ---------------- Onglet 1 : quels chapitres vont tomber ? ----------------
with onglet_chapitres:
    df = charger()
    matiere = st.selectbox("Ta matière", sorted(df["matiere"].unique()))
    r = predire(df, matiere)

    st.subheader(f"Chapitres les plus probables au bac {r['annee']}")
    tableau = pd.DataFrame({"Chapitre": r["chapitres"].index, "Probabilité (%)": r["chapitres"].values})
    st.bar_chart(tableau, x="Chapitre", y="Probabilité (%)", horizontal=True)
    st.dataframe(tableau, hide_index=True, width="stretch")

    col1, col2 = st.columns(2)
    col1.metric("Fiabilité mesurée", f"{r['fiabilite']} %", f"{r['fiabilite'] - r['hasard']:+} pts vs hasard")
    col2.metric("Au hasard", f"{r['hasard']} %")
    with st.expander("Comment est calculée la fiabilité ?"):
        st.write(
            f"On a caché les années 2022 à 2026 une par une, prédit leurs chapitres avec les années "
            f"précédentes, puis compté les bons chapitres. Modèle retenu : **{r['modele']}**."
        )
        st.write({nom: f"{taux} %" for nom, taux in r["comparaison"].items()})

# ---------------- Onglet 2 : sujet d'entraînement à partir de PDF ----------------
with onglet_sujet:
    st.write("Dépose au moins 2 anciens sujets en PDF : ExamPredict assemble un sujet d'entraînement "
             "avec de vrais exercices sur les thèmes les plus fréquents.")
    st.caption("Version actuelle : sujets de physique-chimie dont les exercices s'intitulent « Exercice N - titre (X points) ».")
    fichiers = st.file_uploader("Tes sujets en PDF", type="pdf", accept_multiple_files=True)

    if st.button("Générer mon sujet", type="primary", disabled=not fichiers):
        with st.spinner("Analyse des sujets en cours..."):
            with tempfile.TemporaryDirectory() as dossier:
                for fichier in fichiers:
                    (Path(dossier) / fichier.name).write_bytes(fichier.getvalue())
                sortie = Path(dossier) / "sujet_probable.pdf"
                try:
                    scores, choisis = generer(dossier, sortie)
                except ValueError as erreur:
                    st.error(str(erreur))
                    st.stop()
                pdf = sortie.read_bytes()
        st.success("Ton sujet est prêt !")
        for s, ex, note in choisis:
            st.write(f"**{ex['titre']}** ({ex['points']:g} pts) · sujet {s['annee']}, exercice {ex['numero']}")
        st.download_button("⬇️ Télécharger le sujet en PDF", pdf,
                           file_name="sujet_probable.pdf", mime="application/pdf")

st.divider()
st.caption("ExamPredict repère des tendances dans les anciens sujets. Il ne connaît pas le contenu réel du prochain examen.")
