# Le site public de PHILIPPE, l'IA d'ExamPredict : « dossier classé » noir et blanc. GRATUIT.
#
# Lancer en local, depuis la racine du projet :
#   py -m streamlit run src/app.py
#
# Chaque demande est rangée dans TON Google Sheet (via un Google Form). Tu envoies ensuite le dossier
# par e-mail. Facultatif : avec GMAIL_ADRESSE et GMAIL_MOT_DE_PASSE, l'envoi devient automatique.
# Réglages SECRETS (jamais sur GitHub) : .streamlit/secrets.toml en local,
# onglet « Secrets » de Streamlit Cloud en ligne :
#   GMAIL_ADRESSE     = "philippe.bac2027@gmail.com"   # la boîte Gmail qui envoie les chapitres
#   GMAIL_MOT_DE_PASSE = "abcd efgh ijkl mnop"         # « mot de passe d'application » Gmail (16 lettres)
#   FORMULAIRE = "https://docs.google.com/forms/d/e/XXXX/formResponse"   # obligatoire
#   CONTACT    = "philippe.bac2027@gmail.com"     # adresse affichée pour les questions et la suppression des données
#   CODE_ADMIN = "..."                            # ton accès au dossier (avec ?admin à la fin du lien)
#   [CHAMPS]                                      # les identifiants « entry.XXXX » de chaque question du Google Form
#   prenom = "entry.111"
#   nom = "entry.222"
#   email = "entry.333"
#   specialites = "entry.555"
#   jour = "entry.666"

import html
import re
import smtplib
from email.message import EmailMessage

import requests
import streamlit as st
import streamlit.components.v1 as components

from moteur import charger
from pronostics import pronostic

st.set_page_config(page_title="Philippe · Dossier Bac 2027", layout="wide", initial_sidebar_state="collapsed")


def reglage(nom, defaut):
    try:
        return st.secrets[nom]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return defaut


FORMULAIRE = reglage("FORMULAIRE", "")
GMAIL_ADRESSE = reglage("GMAIL_ADRESSE", "")
GMAIL_MOT_DE_PASSE = reglage("GMAIL_MOT_DE_PASSE", "")
CHAMPS = dict(reglage("CHAMPS", {}))
CONTACT = reglage("CONTACT", "")
CODE_ADMIN = reglage("CODE_ADMIN", "")
DUREE = int(reglage("DUREE_REVELATION", 10))   # secondes d'affichage des chapitres (vue admin)
MATIERES = {"Physique-chimie": "physique-chimie", "SVT": "svt", "Maths": "maths"}
URL_SITE = "https://heyphilippe-bac.streamlit.app/"
SOUTIENS = ["0 euros", "2 euros", "7 euros"]   # exactement les choix du Google Form
EMAIL_VALIDE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def envoyer_inscription(infos):
    """Envoie l'inscription au Google Form. Renvoie True si Google l'a bien reçue."""
    donnees = {CHAMPS[cle]: valeur for cle, valeur in infos.items() if cle in CHAMPS}
    try:
        reponse = requests.post(FORMULAIRE, data=donnees, timeout=10)
    except requests.RequestException:
        return False
    return reponse.status_code == 200


def texte_chapitres(specialites, jour):
    """Les chapitres pronostiqués pour les spés et le jour choisis, en texte simple."""
    pronos = tous_les_pronostics()
    jours = [1, 2] if jour not in ("Jour 1", "Jour 2") else [int(jour[-1])]
    blocs = []
    for nom in specialites:
        for j in jours:
            lignes = "\n".join(f"  Exercice {n} : {chap}" for n, chap, origine in pronos[(MATIERES[nom], j)])
            blocs.append(f"{nom.upper()} · JOUR {j}\n{lignes}")
    return "\n\n".join(blocs)


def envoyer_email(infos):
    """Envoie les chapitres à l'élève, et une copie de l'inscription à Philippe. True si c'est parti."""
    corps = (
        f"Bonjour {infos['prenom']},\n\n"
        "Voici ton dossier. Philippe a calculé un chapitre pour chaque exercice de ton épreuve :\n\n"
        f"{texte_chapitres(infos['specialites_liste'], infos['jour'])}\n\n"
        "Commence par ceux-là. Bonne dernière ligne droite.\n\n"
        "Philippe · Bac 2027\n"
        f"{URL_SITE}\n\n"
        "Pour ne plus rien recevoir ou supprimer tes données, réponds simplement à cet e-mail."
    )
    message = EmailMessage()
    message["Subject"] = "Ton dossier Philippe · Bac 2027"
    message["From"] = f"Philippe · Bac 2027 <{GMAIL_ADRESSE}>"
    message["To"] = infos["email"]
    message["Reply-To"] = GMAIL_ADRESSE
    message.set_content(corps)

    copie = EmailMessage()                       # ta liste d'inscrits, dans ta propre boîte
    copie["Subject"] = f"Nouvel inscrit : {infos['prenom']} {infos['nom']} · {infos['specialites']}"
    copie["From"] = GMAIL_ADRESSE
    copie["To"] = GMAIL_ADRESSE
    copie.set_content(
        f"Prénom : {infos['prenom']}\nNom : {infos['nom']}\nE-mail : {infos['email']}\n"
        f"Spés : {infos['specialites']}\nJour : {infos['jour']}"
    )
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as serveur:
            serveur.login(GMAIL_ADRESSE, GMAIL_MOT_DE_PASSE.replace(" ", ""))
            serveur.send_message(message)
            serveur.send_message(copie)
    except (smtplib.SMTPException, OSError):
        return False
    return True


@st.cache_data
def tous_les_pronostics():
    """Calculés une seule fois pour tous les visiteurs (le site tient la charge)."""
    df = charger()
    return {(m, j): pronostic(df, m, j) for m in MATIERES.values() for j in (1, 2)}


STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:wght@400;500;700&display=swap');

:root { --noir: #000; --blanc: #f4f4f1; --gris: #8b8b86; --trait: #2a2a28; color-scheme: dark; }

header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stStatusWidget"],
[data-testid="stHeaderActionElements"] { display: none !important; }
.stApp { background: var(--noir); color: var(--blanc); font-family: 'IBM Plex Mono', ui-monospace, monospace; }
.block-container { max-width: 1120px; padding: 0 20px 60px; }
p, li { font-family: 'IBM Plex Mono', ui-monospace, monospace; }

/* Grain et ligne de balayage, très discrets */
.stApp::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: .07;
  background-image: repeating-linear-gradient(0deg, #fff 0 1px, transparent 1px 3px); }
.stApp::after { content: ""; position: fixed; left: 0; right: 0; height: 120px; pointer-events: none; z-index: 0;
  background: linear-gradient(transparent, rgba(255,255,255,.05), transparent); animation: balaye 7s linear infinite; }
@keyframes balaye { from { top: -120px; } to { top: 100%; } }
.block-container { position: relative; z-index: 1; }

/* Bandeau du haut */
.barre { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; border-bottom: 1px solid var(--trait);
         padding: 16px 0; font-size: .72rem; letter-spacing: .18em; text-transform: uppercase; color: var(--gris); }
.barre b { color: var(--blanc); }
.point { display: inline-block; width: 7px; height: 7px; background: #fff; border-radius: 50%; margin-right: 8px;
         animation: clignote 1.2s steps(2) infinite; }
@keyframes clignote { 50% { opacity: 0; } }

/* Titres */
.titre { font-family: 'Archivo Black', sans-serif !important; font-size: clamp(2.6rem, 7.6vw, 6.4rem); line-height: .92;
         letter-spacing: -0.02em; text-transform: uppercase; margin: 34px 0 10px !important; padding: 0 !important; color: var(--blanc); }
.titre .barre-noire { background: var(--blanc); color: var(--noir); padding: 0 .12em; }
.sous { font-size: clamp(.95rem, 1.7vw, 1.1rem); color: var(--gris); max-width: 62ch; line-height: 1.7; margin: 0 0 18px; }
.sous b { color: var(--blanc); font-weight: 500; }
.etiquette { font-size: .7rem; letter-spacing: .22em; text-transform: uppercase; color: var(--gris); margin: 0 0 12px; }
.entree { animation: monte .9s cubic-bezier(.2,.7,.1,1) both; } .d2 { animation-delay: .12s; } .d3 { animation-delay: .24s; }
@keyframes monte { from { opacity: 0; transform: translateY(26px); } }
@supports (animation-timeline: view()) { .defile { animation: monte linear both; animation-timeline: view(); animation-range: entry 0% cover 25%; } }

/* Tampon */
.tampon { display: inline-block; border: 2px solid var(--blanc); padding: 6px 14px; font-family: 'Archivo Black', sans-serif !important;
          letter-spacing: .25em; font-size: .8rem; transform: rotate(-3deg); animation: frappe .5s .6s cubic-bezier(.3,1.6,.6,1) both; }
@keyframes frappe { from { opacity: 0; transform: rotate(-3deg) scale(2.2); } }

/* Grille du dossier : chapitres caviardés */
.dossier { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--trait); margin: 26px 0; }
.colonne { border-right: 1px solid var(--trait); padding: 18px 18px 8px; min-width: 0; }
.colonne:last-child { border-right: 0; }
.colonne h4 { font-family: 'Archivo Black', sans-serif !important; font-size: 1rem; letter-spacing: .08em; text-transform: uppercase;
              margin: 0 0 12px; padding: 0; color: var(--blanc); }
.ligne { display: grid; grid-template-columns: 74px 1fr; gap: 10px; align-items: center; font-size: .78rem;
         color: var(--gris); padding: 7px 0; border-top: 1px dashed var(--trait); }
.cache { display: block; height: 13px; background: var(--blanc); animation: respire 3s ease-in-out infinite; }
@keyframes respire { 50% { opacity: .55; } }
.jour { font-size: .66rem; letter-spacing: .2em; color: var(--gris); margin: 12px 0 2px; text-transform: uppercase; }
@media (max-width: 780px) { .dossier { grid-template-columns: 1fr; } .colonne { border-right: 0; border-bottom: 1px solid var(--trait); } }

/* Chiffres */
.chiffres { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid var(--trait); margin: 0 0 26px; }
.chiffres div { padding: 18px 16px; border-right: 1px solid var(--trait); min-width: 0; }
.chiffres div:last-child { border-right: 0; }
.chiffres strong { display: block; font-family: 'Archivo Black', sans-serif !important; font-size: clamp(1.6rem, 3.4vw, 2.6rem); line-height: 1; }
.chiffres span { font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: var(--gris); }
@media (max-width: 780px) { .chiffres { grid-template-columns: repeat(2, minmax(0, 1fr)); } .chiffres div { border-bottom: 1px solid var(--trait); } }

/* Arguments */
.raisons { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0; border: 1px solid var(--trait); margin: 0 0 26px; }
.raisons div { padding: 20px 20px; border-bottom: 1px solid var(--trait); border-right: 1px solid var(--trait); min-width: 0; }
.raisons div:nth-child(2n) { border-right: 0; }
.raisons div:nth-last-child(-n+2) { border-bottom: 0; }
.raisons em { font-style: normal; font-family: 'Archivo Black', sans-serif !important; font-size: .95rem; text-transform: uppercase;
              letter-spacing: .04em; display: block; margin-bottom: 6px; color: var(--blanc); }
.raisons p { margin: 0; font-size: .82rem; color: var(--gris); line-height: 1.6; }
@media (max-width: 780px) { .raisons { grid-template-columns: 1fr; } .raisons div { border-right: 0 !important; border-bottom: 1px solid var(--trait) !important; } }

/* Bloc d'accès */
.merci { text-align: center; padding: 6px 0 4px; }
.merci .etiquette { display: inline-block; }
.merci-titre { font-family: 'Archivo Black', sans-serif !important; font-size: clamp(2rem, 6vw, 3rem);
  line-height: 1.02; text-transform: uppercase; margin: 14px 0 12px; color: var(--blanc); }
.merci p { color: var(--blanc); font-size: 1rem; line-height: 1.5; }
.acces { border: 1px solid var(--blanc); padding: 22px 22px 6px; margin: 0 0 14px; }
.virement { display: grid; gap: 8px; margin: 14px 0 6px; }
.virement div { display: grid; grid-template-columns: 170px 1fr; gap: 12px; border-top: 1px dashed var(--trait); padding-top: 8px; }
.virement span { font-size: .7rem; letter-spacing: .18em; text-transform: uppercase; color: var(--gris); }
.virement b { font-weight: 500; letter-spacing: .06em; overflow-wrap: anywhere; }
@media (max-width: 600px) { .virement div { grid-template-columns: 1fr; gap: 2px; } }
.prix { font-family: 'Archivo Black', sans-serif !important; font-size: clamp(2.4rem, 6vw, 4rem); line-height: 1; }

/* Widgets Streamlit */
.stButton > button, .stLinkButton > a, [data-testid="stFormSubmitButton"] > button {
  font-family: 'Archivo Black', sans-serif !important; letter-spacing: .08em; text-transform: uppercase; font-size: .95rem !important;
  background: var(--blanc) !important; color: var(--noir) !important; border: 0 !important; border-radius: 0 !important;
  padding: .9rem 1.8rem !important; transition: transform .2s ease, box-shadow .2s ease; }
.stButton > button:hover, .stLinkButton > a:hover, [data-testid="stFormSubmitButton"] > button:hover {
  transform: translate(-3px, -3px); box-shadow: 6px 6px 0 #6b6b67; }
.stButton > button:focus-visible, .stLinkButton > a:focus-visible { outline: 2px solid var(--blanc); outline-offset: 4px; }
[data-testid="stTextInput"] input { background: #0c0c0b !important; color: var(--blanc) !important; border-radius: 0 !important;
  font-family: 'IBM Plex Mono', monospace !important; letter-spacing: .15em; border: 1px solid var(--trait) !important; }
[data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p { color: var(--blanc) !important; }
[data-testid="stCaptionContainer"] { color: var(--gris) !important; }
[data-testid="stWidgetLabel"] p { font-size: .7rem !important; letter-spacing: .2em; text-transform: uppercase; color: var(--gris) !important; }
[data-testid="stButtonGroup"] button { border-radius: 0 !important; background: transparent !important; color: var(--blanc) !important;
  border: 1px solid var(--trait) !important; font-family: 'IBM Plex Mono', monospace !important; letter-spacing: .1em; text-transform: uppercase; }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-pressed="true"],
[data-testid="stButtonGroup"] button[kind$="Active"] {
  background: var(--blanc) !important; color: var(--noir) !important; }

/* Résultats déclassifiés */
.resultat { display: grid; grid-template-columns: 92px 1fr; gap: 18px; align-items: center; border: 1px solid var(--trait);
            border-left: 4px solid var(--blanc); padding: 18px 22px; margin-bottom: 10px; position: relative; overflow: hidden;
            animation: monte .7s both; animation-delay: calc(var(--i) * .12s); }
.resultat::after { content: ""; position: absolute; inset: 0; background: var(--blanc); transform-origin: right;
                   animation: leve .8s cubic-bezier(.7,0,.2,1) both; animation-delay: calc(.3s + var(--i) * .18s); }
@keyframes leve { to { transform: scaleX(0); } }
.resultat .n { font-family: 'Archivo Black', sans-serif !important; font-size: 2.6rem; line-height: 1; }
.resultat .l { font-size: .68rem; letter-spacing: .22em; text-transform: uppercase; color: var(--gris); }
.resultat .c { font-family: 'Archivo Black', sans-serif !important; font-size: clamp(1.15rem, 2.6vw, 1.7rem); text-transform: uppercase; line-height: 1.15; }

@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

if "debloque" not in st.session_state:
    st.session_state.debloque = False

if "inscrit" not in st.session_state:
    st.session_state.inscrit = False

BARRE = (
    '<div class="barre"><span><span class="point"></span><b>PHILIPPE</b> · l’IA qui a calculé le bac 2027</span>'
    '<span>Accès restreint · Île-de-France</span><span>Physique-chimie · SVT · Maths</span></div>'
)


def grille_cachee():
    """L'aperçu du dossier : les vraies places d'exercices, avec des chapitres caviardés."""
    longueurs = [82, 64, 91, 57, 76, 69, 88, 61]
    colonnes = ""
    for i, (nom, nb) in enumerate([("Physique-chimie", 3), ("SVT", 2), ("Maths", 4)]):
        lignes = ""
        for jour in (1, 2):
            lignes += f'<div class="jour">Jour {jour}</div>'
            for e in range(1, nb + 1):
                largeur = longueurs[(i * 3 + jour * 2 + e) % len(longueurs)]
                lignes += (f'<div class="ligne"><span>EXERCICE {e}</span>'
                           f'<span class="cache" style="width:{largeur}%"></span></div>')
        colonnes += f'<div class="colonne"><h4>{nom}</h4>{lignes}</div>'
    return f'<div class="dossier defile">{colonnes}</div>'


@st.dialog(" ", width="medium")
def fenetre_merci(prenom):
    """La fenêtre qui se superpose au site juste après la demande."""
    st.markdown(
        '<div class="merci"><div class="etiquette">Demande reçue</div>'
        f'<div class="merci-titre">Merci à toi,<br>{html.escape(prenom)}.</div>'
        '<p>Tu vas recevoir un <b>e-mail</b> ou un <b>SMS</b> avec les éléments de ta demande.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("Fermer", width="stretch"):
        st.rerun()


def bloc_inscription():
    if st.session_state.inscrit:
        if st.session_state.pop("fenetre", None):      # une seule fois, juste après l'envoi
            fenetre_merci(st.session_state.prenom)
        st.markdown(
            '<div class="acces"><div class="etiquette">Demande reçue</div>'
            '<div class="prix">C’est noté.</div>'
            f'<p class="sous">Ta demande est enregistrée. Philippe t’envoie ton dossier à '
            f'<b>{st.session_state.inscrit}</b>. Surveille ta boîte mail (et tes spams).</p></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="acces"><div class="etiquette">Accès au dossier</div>'
        '<div class="prix">Gratuit.</div>'
        '<p class="sous">Fais ta demande : Philippe t’envoie <b>ton dossier par e-mail</b>, tes chapitres exercice par exercice, '
        'pour ta spé et ton jour.</p></div>',
        unsafe_allow_html=True,
    )
    with st.form("inscription", border=False):
        col1, col2 = st.columns(2)
        prenom = col1.text_input("Prénom *")
        nom = col2.text_input("Nom *")
        col3, col4 = st.columns(2)
        email = col3.text_input("E-mail * (Philippe t’y envoie ton dossier)")
        telephone = col4.text_input("Téléphone *")
        specialites = st.pills("Tes spés *", list(MATIERES), selection_mode="multi")
        jour = st.radio("Ton jour d’épreuve", ["Jour 1", "Jour 2", "Je ne sais pas encore"], horizontal=True)
        soutien = st.radio("Soutenir Hey Philippe à hauteur de", SOUTIENS, horizontal=True)
        accord = st.checkbox(
            "J’accepte que ces informations servent uniquement à m’envoyer les pronostics de Philippe. "
            "Elles ne sont ni vendues ni partagées, et je peux demander leur suppression à tout moment."
        )
        if st.form_submit_button("Demander mon dossier", width="stretch"):
            manque = [libelle for libelle, ok in [
                ("ton prénom", prenom.strip()),
                ("ton nom", nom.strip()),
                ("un e-mail valide", EMAIL_VALIDE.match(email.strip())),
                ("ton téléphone", len(re.sub(r"\D", "", telephone)) >= 8),
                ("au moins une spé (clique dessus : elle devient blanche)", specialites),
            ] if not ok]
            if manque:
                st.error("Il manque " + ", ".join(manque) + ".")
            elif not accord:
                st.error("Coche la case d’accord pour envoyer ta demande.")
            else:
                infos = {
                    "prenom": prenom.strip(), "nom": nom.strip(), "email": email.strip(),
                    "telephone": telephone.strip(),
                    "specialites": ", ".join(specialites) + " · " + jour,   # le jour va dans la colonne SPE
                    "specialites_liste": list(specialites), "jour": jour, "soutien": soutien,
                }
                ok = FORMULAIRE and envoyer_inscription(
                    {k: v for k, v in infos.items() if k != "specialites_liste"})
                if ok:
                    if GMAIL_ADRESSE and GMAIL_MOT_DE_PASSE:      # envoi automatique, seulement s'il est configuré
                        envoyer_email(infos)
                    st.session_state.inscrit = infos["email"]
                    st.session_state.prenom = infos["prenom"]
                    st.session_state.fenetre = True
                    st.rerun()
                else:
                    st.error("Ta demande n’est pas passée. Réessaie dans un instant.")
    if CONTACT:
        st.caption(f"Une question, ou supprimer tes données : {CONTACT}")

    if "admin" in st.query_params and CODE_ADMIN:      # visible seulement avec ?admin dans le lien
        with st.form("admin", border=False):
            mot = st.text_input("Accès admin", type="password")
            if st.form_submit_button("Entrer"):
                if mot.strip() == CODE_ADMIN:
                    st.session_state.debloque = True
                    st.rerun()
                else:
                    st.error("Code refusé.")


def page_intro():
    st.markdown(BARRE, unsafe_allow_html=True)
    st.markdown(
        '<div class="tampon entree">Classifié</div>'
        '<h1 class="titre entree d2">Le bac 2027<br>est <span class="barre-noire">déjà écrit</span><br>quelque part.</h1>'
        '<p class="sous entree d3"><b>Philippe</b> est une IA. Elle a avalé <b>15 ans de sujets du bac</b>, exercice par exercice. '
        'Elle a sorti <b>un chapitre pour chaque exercice</b> de ton épreuve. Le résultat est ci-dessous. '
        'Caviardé.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(grille_cachee(), unsafe_allow_html=True)

    bloc_inscription()

    st.markdown(
        '<div class="chiffres defile">'
        '<div><strong>15</strong><span>années de sujets</span></div>'
        '<div><strong>3</strong><span>modèles d’IA en compétition</span></div>'
        '<div><strong>18</strong><span>exercices pronostiqués</span></div>'
        '<div><strong>2</strong><span>jours d’épreuve</span></div>'
        '<div><strong>10/13</strong><span>chapitres 2026 retrouvés à l’aveugle</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="raisons defile">'
        '<div><em>Un vrai modèle de machine learning</em><p>Régression logistique, votes pondérés dans le temps, '
        'fréquences : trois modèles mathématiques entraînés sur 15 ans de sujets, mis en compétition. '
        'Le plus précis est devenu Philippe.</p></div>'
        '<div><em>Testé sur le bac 2026</em><p>Sans voir les sujets 2026, Philippe a retrouvé 10 des 13 chapitres tombés. '
        'C’est lui qui a calculé 2027.</p></div>'
        '<div><em>On l’a testé avant de vous le donner</em><p>On ne voulait pas vous vendre une intuition. '
        'On a d’abord mis Philippe à l’épreuve du bac 2026, à l’aveugle. Il a tenu. Cette année, on l’ouvre à tous.</p></div>'
        '<div><em>Coefficient 16</em><p>Chaque spé compte coefficient 16 au bac. C’est là que se joue ta mention. '
        'Ta dernière ligne droite doit viser juste.</p></div>'
        '<div><em>Exercice par exercice</em><p>Pas une liste vague. Exercice 1, exercice 2, exercice 3 : '
        'un chapitre pour chacun, jour 1 et jour 2.</p></div>'
        '<div><em>Révise dans le bon ordre</em><p>Les autres révisent tout au même niveau. '
        'Toi, tu sais par où commencer.</p></div>'
        '<div><em>Envoyé chez toi</em><p>Tu fais ta demande, Philippe t’envoie ton dossier par e-mail. Exercice par exercice, pour ta spé et ton jour.</p></div>'
        '<div><em>Gratuit</em><p>Aucun paiement. Juste ton inscription. Pour l’épreuve qui pèse le plus dans ton bac.</p></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def revelation(chapitres, reference, duree):
    """Le dossier affiché pendant `duree` secondes, dans un cadre protégé :
    filigrane de l'acheteur, floutage si la fenêtre perd le focus, pas de clic droit, de copie ni d'impression."""
    cartes = "".join(
        f'<div class="r"><div class="n">{n:02d}</div><div><div class="l">Exercice {n}</div><div class="c">{c}</div></div></div>'
        for n, c, origine in chapitres
    )
    filigrane = "".join(f"<span>{reference} · PHILIPPE · {reference}</span>" for _ in range(40))
    return (GABARIT_REVELATION.replace("__CARTES__", cartes)
            .replace("__FILIGRANE__", filigrane).replace("__DUREE__", str(duree)))


GABARIT_REVELATION = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:wght@400;500&display=swap');
* { box-sizing: border-box; }
html, body { margin: 0; background: #000; color: #f4f4f1; font-family: 'IBM Plex Mono', monospace;
  -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; overflow: hidden; }
#zone { position: relative; padding: 4px 2px; transition: filter .15s; }
body.flou #zone { filter: blur(22px); }
.temps { display: flex; justify-content: space-between; font-size: 11px; letter-spacing: .2em; text-transform: uppercase; color: #8b8b86; margin-bottom: 8px; }
.temps b { color: #f4f4f1; font-family: 'Archivo Black', sans-serif; font-size: 18px; letter-spacing: 0; }
.barre { height: 3px; background: #2a2a28; margin-bottom: 14px; }
.barre i { display: block; height: 100%; background: #f4f4f1; width: 100%; transition: width .1s linear; }
.r { display: grid; grid-template-columns: 70px 1fr; gap: 14px; align-items: center; border: 1px solid #2a2a28;
     border-left: 4px solid #f4f4f1; padding: 14px 18px; margin-bottom: 8px; }
.n { font-family: 'Archivo Black', sans-serif; font-size: 34px; line-height: 1; }
.l { font-size: 10px; letter-spacing: .22em; text-transform: uppercase; color: #8b8b86; }
.c { font-family: 'Archivo Black', sans-serif; font-size: 20px; text-transform: uppercase; line-height: 1.15; }
.fil { position: absolute; inset: -60px; display: flex; flex-wrap: wrap; gap: 26px 40px; transform: rotate(-18deg);
       opacity: .14; pointer-events: none; font-size: 12px; letter-spacing: .15em; z-index: 2; }
.ferme { height: 100vh; display: grid; place-items: center; text-align: center; font-family: 'Archivo Black', sans-serif;
         text-transform: uppercase; letter-spacing: .2em; font-size: 16px; color: #8b8b86; }
@media print { body { display: none !important; } }
</style>
<div id="zone">
  <div class="temps"><span>Dossier ouvert · ne pas diffuser</span><b id="t">__DUREE__</b></div>
  <div class="barre"><i id="b"></i></div>
  __CARTES__
  <div class="fil">__FILIGRANE__</div>
</div>
<script>
const total = __DUREE__ * 1000, debut = Date.now();
const fermer = () => { document.body.innerHTML = '<div class="ferme">Dossier refermé.</div>'; };
const tic = setInterval(() => {
  const reste = total - (Date.now() - debut);
  if (reste <= 0) { clearInterval(tic); fermer(); return; }
  document.getElementById('t').textContent = Math.ceil(reste / 1000);
  document.getElementById('b').style.width = (reste / total * 100) + '%';
}, 100);
const flou = (on) => document.body.classList.toggle('flou', on);
let parent = null;
try { parent = window.parent; } catch (e) {}
for (const w of [window, parent]) {
  if (!w) continue;
  try {
    w.addEventListener('blur', () => flou(true));
    w.addEventListener('focus', () => flou(false));
    w.document.addEventListener('visibilitychange', () => flou(w.document.hidden));
    w.addEventListener('keydown', (e) => {
      if (e.key === 'PrintScreen' || (e.metaKey && e.shiftKey)) { flou(true); setTimeout(() => flou(false), 1500); }
    });
    w.addEventListener('beforeprint', () => flou(true));
  } catch (e) {}
}
['contextmenu', 'copy', 'cut', 'dragstart', 'selectstart'].forEach(ev => document.addEventListener(ev, e => e.preventDefault()));
</script>
"""


def page_dossier():
    st.markdown(BARRE, unsafe_allow_html=True)
    if st.session_state.get("ferme"):
        st.markdown(
            '<div class="tampon">Refermé</div>'
            '<h1 class="titre" style="font-size:clamp(2.2rem,6vw,4.6rem)">Le dossier<br>s’est refermé.</h1>'
            '<p class="sous">Philippe ne parle qu’une fois. À toi de jouer maintenant.</p>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="tampon entree">Déclassifié</div>'
        '<h1 class="titre entree d2" style="font-size:clamp(2.2rem,6vw,4.6rem)">Philippe va parler.</h1>'
        f'<p class="sous">Choisis ta spé et ton jour. Tu auras <b>{DUREE} secondes</b>, une seule fois. '
        'Prépare-toi à retenir.</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        nom = st.segmented_control("Spécialité", list(MATIERES), default="Physique-chimie")
    with col2:
        jour = st.segmented_control("Jour", [1, 2], default=1, format_func=lambda j: f"Jour {j}")
    if not nom or not jour:
        return

    if st.button(f"Révéler · {DUREE} secondes", width="stretch"):
        st.session_state.ferme = True          # au prochain rechargement, le dossier est refermé
        chapitres = tous_les_pronostics()[(MATIERES[nom], jour)]
        components.html(revelation(chapitres, "ADMIN", DUREE),
                        height=96 + 92 * len(chapitres))


if st.session_state.debloque:
    page_dossier()
else:
    page_intro()
