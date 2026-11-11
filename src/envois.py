# Prépare les e-mails de TOUTES les demandes du Google Sheet, avec le lien personnel de chaque élève.
#
# 1. Google Sheet > Fichier > Télécharger > Valeurs séparées par des virgules (.csv)
# 2. Depuis la racine du projet :
#      py src/envois.py "C:/Users/josep/Downloads/Philippe (réponses) - Réponses au formulaire 1.csv"
# 3. Ouvre data/analyses/envois.html : un bouton « Envoyer » par élève ouvre l'e-mail déjà écrit.
#
# Les liens sont signés avec la même clé que le site (CODE_ADMIN dans .streamlit/secrets.toml) :
# ils s'ouvrent sur https://heyphilippe-bac.streamlit.app/ avec les chapitres de l'élève dévoilés.

import base64
import csv
import hashlib
import hmac
import html
import json
import sys
import tomllib
from pathlib import Path
from urllib.parse import quote

RACINE = Path(__file__).resolve().parent.parent
URL_SITE = "https://heyphilippe-bac.streamlit.app/"
MATIERES = {"physique": "physique-chimie", "svt": "svt", "maths": "maths"}
SORTIE = RACINE / "data" / "analyses" / "envois.html"     # dossier ignoré par Git : données personnelles


def cle():
    secrets = tomllib.loads((RACINE / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
    return secrets.get("CLE_LIENS") or secrets["CODE_ADMIN"]


def creer_lien(prenom, codes, jours, cle_liens):
    """Exactement le même lien que le générateur de l'admin du site."""
    donnees = json.dumps({"p": prenom, "s": codes, "j": jours}, separators=(",", ":"), ensure_ascii=False)
    contenu = base64.urlsafe_b64encode(donnees.encode()).decode().rstrip("=")
    signe = hmac.new(cle_liens.encode(), contenu.encode(), hashlib.sha256).hexdigest()[:20]
    return f"{URL_SITE}?d={contenu}.{signe}"


def colonne(ligne, debut):
    """La valeur de la colonne dont le titre commence par `debut` (PRENOM, EMAIL, SPE…)."""
    for titre, valeur in ligne.items():
        if titre and titre.strip().upper().startswith(debut):
            return (valeur or "").strip()
    return ""


def lire_demande(ligne):
    spe = colonne(ligne, "SPE").lower()                    # ex. « maths, svt · jour 1 »
    codes = [code for mot, code in MATIERES.items() if mot in spe]
    jours = [1] if "jour 1" in spe else [2] if "jour 2" in spe else [1, 2]
    return colonne(ligne, "PRENOM"), colonne(ligne, "EMAIL"), codes, jours, colonne(ligne, "SOUTENIR")


def message(prenom, lien, soutien):
    texte = (
        f"Salut {prenom},\n\n"
        "Ton dossier Philippe est prêt. Tes chapitres du bac 2027, exercice par exercice, "
        "sont dévoilés sur ta page personnelle :\n\n"
        f"{lien}\n\n"
        "Ce lien est personnel, garde-le pour toi.\n"
    )
    if soutien and not soutien.startswith("0"):
        texte += f"\nMerci pour ton soutien ({soutien}) ! Je t'envoie comment le faire dans un prochain message.\n"
    return texte + "\nBonne dernière ligne droite,\nPhilippe · Bac 2027"


def main(chemin_csv):
    cle_liens = cle()
    with open(chemin_csv, encoding="utf-8-sig", newline="") as f:
        demandes = [lire_demande(ligne) for ligne in csv.DictReader(f)]

    cartes, ignorees = "", 0
    for prenom, email, codes, jours, soutien in demandes:
        if not prenom or "@" not in email or not codes:
            ignorees += 1
            continue
        lien = creer_lien(prenom, codes, jours, cle_liens)
        corps = message(prenom, lien, soutien)
        mailto = f"mailto:{email}?subject={quote('Ton dossier Philippe · Bac 2027')}&body={quote(corps)}"
        gmail = ("https://mail.google.com/mail/?view=cm&fs=1"
                 f"&to={quote(email)}&su={quote('Ton dossier Philippe · Bac 2027')}&body={quote(corps)}")
        cartes += f"""
<div class="carte">
  <div class="haut"><b>{html.escape(prenom)}</b><span>{html.escape(email)}</span></div>
  <div class="spe">{html.escape(', '.join(codes))} · jour {' et '.join(map(str, jours))}
    {('· soutien ' + html.escape(soutien)) if soutien else ''}</div>
  <a class="bouton" href="{html.escape(gmail)}" target="_blank">Envoyer avec Gmail</a>
  <a class="bouton clair" href="{html.escape(mailto)}">Autre messagerie</a>
  <a class="bouton clair" href="{html.escape(lien)}" target="_blank">Voir sa page</a>
  <label><input type="checkbox"> Envoyé</label>
</div>"""

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Envois Philippe</title>
<style>
body {{ background:#000; color:#f4f4f1; font-family:Consolas, monospace; max-width:900px; margin:0 auto; padding:24px 16px; }}
h1 {{ font-family:'Arial Black', sans-serif; text-transform:uppercase; font-size:clamp(1.4rem, 6vw, 2.4rem); }}
* {{ box-sizing:border-box; overflow-wrap:anywhere; }}
.carte {{ border:1px solid #2a2a28; border-left:4px solid #f4f4f1; padding:14px 16px; margin:10px 0; }}
.haut {{ display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; }}
.haut span, .spe {{ color:#8b8b86; font-size:.85rem; }} .spe {{ margin:6px 0 12px; text-transform:uppercase; }}
.bouton {{ display:inline-block; background:#f4f4f1; color:#000; padding:8px 14px; text-decoration:none;
  font-weight:bold; margin:0 6px 6px 0; }}
.bouton.clair {{ background:none; color:#f4f4f1; border:1px solid #f4f4f1; }}
label {{ color:#8b8b86; margin-left:6px; }}
</style></head><body>
<h1>Envois · {len(demandes) - ignorees} élèves</h1>
<p style="color:#8b8b86">Clique sur « Envoyer avec Gmail » : l'e-mail est déjà écrit, il ne reste qu'à appuyer sur Envoyer.</p>
{cartes}
</body></html>""", encoding="utf-8")
    print(f"{len(demandes) - ignorees} e-mails prêts, {ignorees} ligne(s) ignorée(s) (prénom, e-mail ou spé manquant).")
    print("Ouvre :", SORTIE)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage : py src/envois.py "chemin/vers/le/fichier.csv"')
    main(sys.argv[1])
