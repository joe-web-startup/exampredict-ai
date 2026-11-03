# Le site public d'ExamPredict AI
#
# Lancer en local, depuis la racine du projet :
#   py -m streamlit run src/app.py
#
# Réglage secret (fichier .streamlit/secrets.toml en local, onglet « Secrets » en ligne) :
#   LIEN_PAIEMENT = "https://..."   # le lien de paiement (Stripe)
# Sans lien de paiement, le site est en MODE TEST : le bouton débloque directement.

import streamlit as st

from moteur import charger
from pronostics import pronostic

st.set_page_config(page_title="ExamPredict · Bac 2027", layout="wide", initial_sidebar_state="collapsed")


def reglage(nom, defaut):
    try:
        return st.secrets[nom]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return defaut


LIEN_PAIEMENT = reglage("LIEN_PAIEMENT", "")
MATIERES = {"Physique-chimie": "physique-chimie", "SVT": "svt", "Maths": "maths"}

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700;900&family=Manrope:wght@400;500;700&display=swap');

:root {
  --encre: #08090e;
  --texte: #f3f1ec;
  --doux: rgba(243, 241, 236, 0.62);
  --corail: #ff5a36;
  --glace: #8fd3ff;
  --verre: rgba(255, 255, 255, 0.06);
  --bord: rgba(255, 255, 255, 0.14);
  color-scheme: dark;
}

/* --- On retire l'habillage de Streamlit --- */
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stStatusWidget"] { display: none !important; }
.stApp { background: var(--encre); color: var(--texte); font-family: 'Manrope', system-ui, sans-serif; overflow-x: hidden; }
.block-container { max-width: 1080px; padding: 0 20px 120px; }

/* --- Fond : deux nappes de couleur qui dérivent lentement --- */
.stApp::before, .stApp::after {
  content: ""; position: fixed; z-index: 0; border-radius: 50%; filter: blur(110px); opacity: .55; pointer-events: none;
}
.stApp::before { width: 60vw; height: 60vw; background: var(--corail); top: -25vw; left: -15vw; animation: derive 22s ease-in-out infinite alternate; }
.stApp::after  { width: 55vw; height: 55vw; background: var(--glace); bottom: -30vw; right: -20vw; opacity: .35; animation: derive 28s ease-in-out infinite alternate-reverse; }
@keyframes derive { to { transform: translate(12vw, 10vh) scale(1.15); } }
[data-testid="stAppViewContainer"] > .main, .block-container { position: relative; z-index: 1; }

/* --- Typographie --- */
h1.titre, h2.grand { padding: 0 !important; color: var(--texte); }
.titre a, .grand a, [data-testid="stHeaderActionElements"] { display: none !important; }
.titre { font-family: 'Unbounded', sans-serif !important; font-weight: 900; line-height: .95; letter-spacing: -0.03em;
         font-size: clamp(2.8rem, 9vw, 7.5rem); margin: 0; text-wrap: balance; }
.titre em { font-style: normal; color: var(--corail); }
.sur-titre { font-family: 'Unbounded', sans-serif !important; font-weight: 500; letter-spacing: .3em; text-transform: uppercase;
             font-size: .75rem; color: var(--doux); }
.phrase { font-size: clamp(1.1rem, 2.2vw, 1.45rem); color: var(--doux); max-width: 34ch; line-height: 1.5; }
.grand { font-family: 'Unbounded', sans-serif !important; font-weight: 700; font-size: clamp(1.9rem, 5vw, 3.6rem);
         line-height: 1.05; letter-spacing: -0.02em; margin: 0 0 .4em; text-wrap: balance; }

/* --- Sections et apparition au défilement --- */
.ecran { min-height: 92vh; display: flex; flex-direction: column; justify-content: center; gap: 28px; }
.section { min-height: 70vh; display: flex; flex-direction: column; justify-content: center; }
.entree { animation: monte 1.1s cubic-bezier(.2,.7,.1,1) both; }
.entree.d2 { animation-delay: .15s; } .entree.d3 { animation-delay: .3s; } .entree.d4 { animation-delay: .45s; }
@keyframes monte { from { opacity: 0; transform: translateY(48px); filter: blur(10px); } }
@supports (animation-timeline: view()) {
  .defile { animation: apparait linear both; animation-timeline: view(); animation-range: entry 5% cover 35%; }
}
@keyframes apparait { from { opacity: 0; transform: translateY(80px) scale(.94); filter: blur(12px); } }

/* --- Verre --- */
.verre { background: var(--verre); border: 1px solid var(--bord); border-radius: 28px;
         backdrop-filter: blur(22px) saturate(140%); -webkit-backdrop-filter: blur(22px) saturate(140%);
         box-shadow: 0 30px 80px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.12); }
.trio { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.trio .verre { padding: 34px 26px; }
.trio .nom { font-family: 'Unbounded', sans-serif !important; font-weight: 700; font-size: 1.6rem; }
.trio .info { color: var(--doux); margin-top: 8px; }
@media (max-width: 760px) { .trio { grid-template-columns: 1fr; } }

/* --- Bandeau défilant --- */
.bandeau { overflow: hidden; white-space: nowrap; border-block: 1px solid var(--bord); padding: 18px 0; margin: 40px 0; }
.bandeau span { display: inline-block; font-family: 'Unbounded', sans-serif !important; font-weight: 700; font-size: 1.4rem;
                color: transparent; -webkit-text-stroke: 1px rgba(243,241,236,.45); animation: file 26s linear infinite; padding-right: 2rem; }
@keyframes file { to { transform: translateX(-50%); } }

/* --- Boutons Streamlit --- */
.stButton > button, .stLinkButton > a {
  font-family: 'Unbounded', sans-serif !important; font-weight: 700 !important; font-size: 1.05rem !important;
  background: var(--corail) !important; color: #120806 !important; border: 0 !important; border-radius: 999px !important;
  padding: .95rem 2.2rem !important; box-shadow: 0 0 0 0 rgba(255,90,54,.55);
  transition: transform .25s ease, box-shadow .25s ease; animation: pulse 2.4s ease-out infinite;
}
.stButton > button:hover, .stLinkButton > a:hover { transform: translateY(-2px) scale(1.03); }
.stButton > button:focus-visible, .stLinkButton > a:focus-visible { outline: 2px solid var(--glace); outline-offset: 4px; }
@keyframes pulse { 70% { box-shadow: 0 0 0 22px rgba(255,90,54,0); } 100% { box-shadow: 0 0 0 0 rgba(255,90,54,0); } }

/* --- Sélecteurs --- */
[data-testid="stWidgetLabel"] p { font-family: 'Unbounded', sans-serif !important; letter-spacing: .2em; text-transform: uppercase;
                                  font-size: .72rem !important; color: var(--doux) !important; }
[data-testid="stButtonGroup"] button { border-radius: 999px !important; font-family: 'Manrope', sans-serif; font-weight: 700;
                                       background: var(--verre) !important; border: 1px solid var(--bord) !important; color: var(--texte) !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind$="Active"] {
  background: var(--texte) !important; color: var(--encre) !important; }

/* --- Cartes de pronostic --- */
.carte { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: 26px; padding: 30px 34px; margin-bottom: 16px;
         animation: monte .9s cubic-bezier(.2,.7,.1,1) both; animation-delay: calc(var(--i) * .14s); }
.carte .num { font-family: 'Unbounded', sans-serif !important; font-weight: 900; font-size: 3.2rem; color: var(--corail); line-height: 1; }
.carte .lib { font-size: .72rem; letter-spacing: .25em; text-transform: uppercase; color: var(--doux); }
.carte .chap { font-family: 'Unbounded', sans-serif !important; font-weight: 700; font-size: clamp(1.3rem, 3vw, 2rem); line-height: 1.15; }
.note { color: var(--doux); font-size: .8rem; margin-top: 30px; max-width: 70ch; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

if "debloque" not in st.session_state:
    st.session_state.debloque = False


def bouton_decouvrir(cle):
    """Le bouton d'achat : vers le paiement, ou déblocage direct en mode test."""
    if LIEN_PAIEMENT:
        st.link_button("Découvrir · 5 €", LIEN_PAIEMENT)
    elif st.button("Découvrir · 5 €", key=cle):
        st.session_state.debloque = True
        st.rerun()


def page_intro():
    st.markdown(
        '<div class="ecran">'
        '<div class="sur-titre entree">ExamPredict · Bac 2027</div>'
        '<h1 class="titre entree d2">Les chapitres<br>qui vont <em>tomber</em>.</h1>'
        '<p class="phrase entree d3">Physique-chimie, SVT, maths. Jour 1 et jour 2. '
        'Exercice par exercice.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    bouton_decouvrir("haut")

    mots = "PHYSIQUE-CHIMIE · SVT · MATHS · JOUR 1 · JOUR 2 · BAC 2027 · "
    st.markdown(f'<div class="bandeau"><span>{mots * 6}</span><span>{mots * 6}</span></div>',
                unsafe_allow_html=True)

    st.markdown(
        '<div class="section defile">'
        '<h2 class="grand">Un modèle entraîné sur les sujets des années passées.</h2>'
        '<p class="phrase">Il a appris quels chapitres reviennent, et à quelle place. '
        'Il te donne son pronostic pour 2027.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section defile"><div class="trio">'
        '<div class="verre"><div class="nom">Physique-chimie</div><div class="info">3 exercices · jour 1 et jour 2</div></div>'
        '<div class="verre"><div class="nom">SVT</div><div class="info">2 exercices · jour 1 et jour 2</div></div>'
        '<div class="verre"><div class="nom">Maths</div><div class="info">4 exercices · jour 1 et jour 2</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section defile">'
        '<h2 class="grand">Prends de l\'avance<br>sur la dernière ligne droite.</h2>'
        '</div>',
        unsafe_allow_html=True,
    )
    bouton_decouvrir("bas")
    st.markdown('<p class="note">Pronostics calculés par un modèle à partir des anciens sujets. '
                'Ils orientent tes révisions et ne garantissent pas le contenu de l\'épreuve.</p>',
                unsafe_allow_html=True)


def page_pronostics():
    st.markdown(
        '<div style="padding-top:12vh"><div class="sur-titre entree">ExamPredict · Bac 2027 · Île-de-France</div>'
        '<h1 class="titre entree d2" style="font-size:clamp(2.2rem,6vw,4.8rem)">Tes <em>chapitres</em>.</h1></div>',
        unsafe_allow_html=True,
    )
    nom = st.segmented_control("Spécialité", list(MATIERES), default="Physique-chimie")
    jour = st.segmented_control("Jour", [1, 2], default=1, format_func=lambda j: f"Jour {j}")
    if not nom or not jour:
        return

    cartes = "".join(
        f'<div class="carte verre" style="--i:{numero}">'
        f'<div class="num">{numero:02d}</div>'
        f'<div><div class="lib">Exercice {numero}</div><div class="chap">{chapitre}</div></div></div>'
        for numero, chapitre, origine in pronostic(charger(), MATIERES[nom], jour)
    )
    st.markdown(f'<div style="margin-top:28px" key="{nom}{jour}">{cartes}</div>', unsafe_allow_html=True)
    st.markdown('<p class="note">Pronostics calculés par un modèle à partir des anciens sujets. '
                'Révise aussi le reste du programme.</p>', unsafe_allow_html=True)


if st.session_state.debloque:
    page_pronostics()
else:
    page_intro()
