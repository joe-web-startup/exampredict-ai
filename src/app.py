# Le site public d'ExamPredict AI : « dossier classé » noir et blanc.
#
# Lancer en local, depuis la racine du projet :
#   py -m streamlit run src/app.py
#
# Réglages SECRETS (jamais sur GitHub) : .streamlit/secrets.toml en local,
# onglet « Secrets » de Streamlit Cloud en ligne :
#   LIEN_PAIEMENT = "https://revolut.me/..."   # ton lien de paiement
#   CODE_ADMIN    = "..."                      # ton code personnel
#   CODES_ACCES   = ["...", "..."]             # codes donnés aux élèves après paiement
# Sans réglage, le site est en MODE TEST et accepte le code TEST2027.

import streamlit as st

from moteur import charger
from pronostics import pronostic

st.set_page_config(page_title="ExamPredict · Dossier Bac 2027", layout="wide", initial_sidebar_state="collapsed")


def reglage(nom, defaut):
    try:
        return st.secrets[nom]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return defaut


LIEN_PAIEMENT = reglage("LIEN_PAIEMENT", "")
CODE_ADMIN = reglage("CODE_ADMIN", "")
CODES_ACCES = {c.strip().upper() for c in reglage("CODES_ACCES", [])}
MODE_TEST = not (CODE_ADMIN or CODES_ACCES)
if MODE_TEST:
    CODES_ACCES = {"TEST2027"}
MATIERES = {"Physique-chimie": "physique-chimie", "SVT": "svt", "Maths": "maths"}


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
.acces { border: 1px solid var(--blanc); padding: 22px 22px 6px; margin: 0 0 14px; }
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
[data-testid="stWidgetLabel"] p { font-size: .7rem !important; letter-spacing: .2em; text-transform: uppercase; color: var(--gris) !important; }
[data-testid="stButtonGroup"] button { border-radius: 0 !important; background: transparent !important; color: var(--blanc) !important;
  border: 1px solid var(--trait) !important; font-family: 'IBM Plex Mono', monospace !important; letter-spacing: .1em; text-transform: uppercase; }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind$="Active"] {
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

.note { color: var(--gris); font-size: .7rem; letter-spacing: .04em; line-height: 1.6; margin-top: 18px; max-width: 90ch; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

if "debloque" not in st.session_state:
    st.session_state.debloque = False

BARRE = (
    '<div class="barre"><span><span class="point"></span><b>ExamPredict</b> · dossier bac 2027</span>'
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


def bloc_acces():
    st.markdown(
        '<div class="acces"><div class="etiquette">Accès au dossier</div>'
        '<div class="prix">5 €</div>'
        '<p class="sous">Paiement unique. Tu reçois ton code d’accès, tu entres, tu choisis ta spé et ton jour.</p></div>',
        unsafe_allow_html=True,
    )
    col_payer, col_code = st.columns([1, 1.2], vertical_alignment="bottom")
    with col_payer:
        if LIEN_PAIEMENT:
            st.link_button("Payer 5 € · Revolut", LIEN_PAIEMENT, width="stretch")
        elif MODE_TEST:
            st.caption("Mode test : paiement non branché. Code : TEST2027")
        else:
            st.caption("Paiement bientôt disponible.")
    with col_code:
        with st.form("acces", border=False):
            code = st.text_input("Code d'accès", placeholder="XXXX-XXXX")
            if st.form_submit_button("Ouvrir le dossier", width="stretch"):
                saisi = code.strip().upper()
                if saisi and (saisi in CODES_ACCES or (CODE_ADMIN and saisi == CODE_ADMIN.upper())):
                    st.session_state.debloque = True
                    st.rerun()
                else:
                    st.error("Code refusé.")


def page_intro():
    st.markdown(BARRE, unsafe_allow_html=True)
    st.markdown(
        '<div class="tampon entree">Classifié</div>'
        '<h1 class="titre entree d2">Le bac 2027<br>est <span class="barre-noire">déjà écrit</span><br>quelque part.</h1>'
        '<p class="sous entree d3">On a fait tourner une IA sur <b>15 ans de sujets du bac</b>, exercice par exercice. '
        'Elle a sorti <b>un chapitre pour chaque exercice</b> de ton épreuve. Le résultat est ci-dessous. '
        'Caviardé.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(grille_cachee(), unsafe_allow_html=True)

    bloc_acces()

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
        '<div><em>Le bac a des habitudes</em><p>Certains chapitres reviennent, toujours à la même place. '
        'Le modèle les a repérées sur 15 ans.</p></div>'
        '<div><em>Testé sur le bac 2026</em><p>Sans voir les sujets 2026, il a retrouvé 10 des 13 chapitres tombés. '
        'Le même modèle a calculé 2027.</p></div>'
        '<div><em>Exercice par exercice</em><p>Pas une liste vague. Exercice 1, exercice 2, exercice 3 : '
        'un chapitre pour chacun, jour 1 et jour 2.</p></div>'
        '<div><em>Révise dans le bon ordre</em><p>Les autres révisent tout au même niveau. '
        'Toi, tu sais par où commencer.</p></div>'
        '<div><em>Instantané</em><p>Code entré, dossier ouvert. Ta spé, ton jour, tes chapitres.</p></div>'
        '<div><em>5 €</em><p>Le prix d’un sandwich. Pour la dernière ligne droite de ton année.</p></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<p class="note">Pronostics calculés à partir des anciens sujets : un ordre de priorité, pas le sujet. '
                'Révise aussi le reste du programme.</p>', unsafe_allow_html=True)


def page_dossier():
    st.markdown(BARRE, unsafe_allow_html=True)
    st.markdown(
        '<div class="tampon entree">Déclassifié</div>'
        '<h1 class="titre entree d2" style="font-size:clamp(2.2rem,6vw,4.6rem)">Ton dossier.</h1>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        nom = st.segmented_control("Spécialité", list(MATIERES), default="Physique-chimie")
    with col2:
        jour = st.segmented_control("Jour", [1, 2], default=1, format_func=lambda j: f"Jour {j}")
    if not nom or not jour:
        return

    lignes = "".join(
        f'<div class="resultat" style="--i:{n}"><div class="n">{n:02d}</div>'
        f'<div><div class="l">Exercice {n}</div><div class="c">{chapitre}</div></div></div>'
        for n, chapitre, origine in tous_les_pronostics()[(MATIERES[nom], jour)]
    )
    st.markdown(f'<div style="margin-top:18px">{lignes}</div>', unsafe_allow_html=True)
    st.markdown('<p class="note">Pronostics calculés à partir des anciens sujets : un ordre de priorité, pas le sujet. '
                'Révise aussi le reste du programme.</p>', unsafe_allow_html=True)


if st.session_state.debloque:
    page_dossier()
else:
    page_intro()
