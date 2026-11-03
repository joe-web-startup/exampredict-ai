# Le site public d'ExamPredict AI
#
# Lancer en local, depuis la racine du projet :
#   py -m streamlit run src/app.py
#
# Réglages secrets (fichier .streamlit/secrets.toml en local, onglet « Secrets » en ligne) :
#   LIEN_PAIEMENT = "https://..."           # le lien de paiement (Stripe)
#   CODES_ACCES = ["CODE1", "CODE2"]        # codes qui débloquent les pronostics
# Sans réglage, le site fonctionne en MODE TEST avec le code TEST2027.

import streamlit as st

from moteur import charger
from pronostics import pronostic

st.set_page_config(page_title="ExamPredict · Bac 2027", page_icon="🎯")


def reglage(nom, defaut):
    """Lit un réglage secret, avec une valeur par défaut s'il n'existe pas."""
    try:
        return st.secrets[nom]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return defaut


LIEN_PAIEMENT = reglage("LIEN_PAIEMENT", "")
CODES_ACCES = set(reglage("CODES_ACCES", ["TEST2027"]))
MATIERES = {"Physique-chimie": "physique-chimie", "SVT": "svt", "Maths": "maths"}

if "debloque" not in st.session_state:
    st.session_state.debloque = False


def page_intro():
    st.title("🎯 Bac 2027 : les chapitres à travailler en priorité")
    st.markdown("#### Physique-chimie · SVT · Maths · Île-de-France · Jour 1 et jour 2")
    st.markdown(
        "**15 ans de sujets du bac analysés par l'IA.** ExamPredict a étudié tous les sujets de "
        "Métropole de 2010 à 2026 et a calculé, **exercice par exercice**, les chapitres les plus "
        "probables pour le bac 2027."
    )
    st.markdown(
        "- ✅ **Ta spé et ton jour** : PC, SVT ou maths, jour 1 ou jour 2\n"
        "- ✅ **Un pronostic par exercice** : « Exercice 1 → … », « Exercice 2 → … »\n"
        "- ✅ **Construit avec du machine learning et testé sur les vrais bacs** : en physique-chimie, "
        "nos pronostics retrouvaient **environ 1 chapitre sur 2** sur les bacs 2023 à 2026, contre "
        "**1 sur 3** en devinant au hasard\n"
        "- ✅ **Accès immédiat** après le paiement"
    )

    st.subheader("🔓 Débloque tes pronostics : 5 €")
    if LIEN_PAIEMENT:
        st.link_button("Payer 5 € (paiement sécurisé)", LIEN_PAIEMENT, type="primary")
        st.caption("Après le paiement, ton code d'accès s'affiche : entre-le ci-dessous.")
    else:
        st.info("Mode test : le paiement n'est pas encore branché. Utilise le code TEST2027.")

    code = st.text_input("Ton code d'accès").strip().upper()
    if st.button("Débloquer"):
        if code in CODES_ACCES:
            st.session_state.debloque = True
            st.rerun()
        else:
            st.error("Code invalide. Vérifie ton code, ou contacte-nous si tu as payé.")

    st.caption(
        "ExamPredict calcule des pronostics à partir des anciens sujets : personne ne connaît le "
        "sujet 2027 à l'avance. Sers-t'en pour choisir tes priorités dans la dernière ligne droite, "
        "sans faire d'impasse sur le reste du programme."
    )


def page_pronostics():
    st.title("🎯 Tes pronostics · Bac 2027")
    st.caption("Métropole (Île-de-France)")
    col1, col2 = st.columns(2)
    nom = col1.selectbox("Ta spécialité", list(MATIERES))
    jour = col2.radio("Ton jour d'épreuve", [1, 2], format_func=lambda j: f"Jour {j}", horizontal=True)

    if st.button("OK", type="primary"):
        st.session_state.choix = (MATIERES[nom], jour)

    if "choix" in st.session_state:
        matiere, jour_choisi = st.session_state.choix
        st.subheader(f"{nom} · Jour {jour_choisi}")
        for numero, chapitre, origine in pronostic(charger(), matiere, jour_choisi):
            st.markdown(f"### Exercice {numero} → {chapitre}")
        st.caption(
            "Pronostics calculés à partir des sujets de Métropole 2010-2026. Ils indiquent les "
            "chapitres à travailler en priorité et ne remplacent pas la révision de tout le programme."
        )


if st.session_state.debloque:
    page_pronostics()
else:
    page_intro()
