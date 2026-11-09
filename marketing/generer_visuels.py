# Génère le QR code et les visuels à imprimer de Philippe.
#   py marketing/generer_visuels.py
# Résultat : marketing/qr_philippe.png, carte_visite.png (85 × 55 mm), autocollant.png (60 × 60 mm), en 300 dpi.

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

URL = "https://heyphilippe-bac.streamlit.app/"
DOSSIER = Path(__file__).parent
DPI = 300
NOIR, BLANC, GRIS = (0, 0, 0), (244, 244, 241), (139, 139, 134)
TITRE = "C:/Windows/Fonts/ariblk.ttf"     # Arial Black, proche du style du site
MONO = "C:/Windows/Fonts/consola.ttf"      # Consolas, pour l'effet « dossier »


def mm(valeur):
    return round(valeur / 25.4 * DPI)


def qr(taille_px):
    """QR code noir sur blanc, correction d'erreur forte (lisible même un peu abîmé)."""
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=2, box_size=20)
    code.add_data(URL)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white").convert("RGB")
    return image.resize((taille_px, taille_px), Image.NEAREST)


def police(chemin, taille):
    return ImageFont.truetype(chemin, taille)


def carte_visite():
    largeur, hauteur = mm(85), mm(55)
    carte = Image.new("RGB", (largeur, hauteur), NOIR)
    d = ImageDraw.Draw(carte)
    marge = mm(5)
    cote = mm(38)
    carte.paste(qr(cote), (largeur - marge - cote, (hauteur - cote) // 2))
    x = marge
    d.text((x, marge), "● PHILIPPE · DOSSIER BAC 2027", font=police(MONO, 24), fill=GRIS)
    y = marge + mm(7)
    for ligne in ["LE BAC 2027", "EST DÉJÀ", "ÉCRIT."]:
        d.text((x, y), ligne, font=police(TITRE, 46), fill=BLANC)
        y += 54
    d.rectangle([x, y + 14, x + 210, y + 58], fill=BLANC)
    d.text((x + 12, y + 18), "SCANNE.", font=police(TITRE, 30), fill=NOIR)
    d.text((x, hauteur - marge - 26), "PC · SVT · MATHS · GRATUIT", font=police(MONO, 22), fill=GRIS)
    carte.save(DOSSIER / "carte_visite.png", dpi=(DPI, DPI))


def autocollant():
    cote = mm(60)
    sticker = Image.new("RGB", (cote, cote), NOIR)
    d = ImageDraw.Draw(sticker)
    marge = mm(5)
    taille_qr = mm(38)
    sticker.paste(qr(taille_qr), ((cote - taille_qr) // 2, mm(12)))
    for texte, y, fnt, couleur in [
        ("CLASSIFIÉ", marge - 10, police(TITRE, 50), BLANC),
        ("PHILIPPE · BAC 2027 · SCANNE", cote - marge - 34, police(MONO, 30), GRIS),
    ]:
        largeur_texte = d.textlength(texte, font=fnt)
        d.text(((cote - largeur_texte) / 2, y), texte, font=fnt, fill=couleur)
    sticker.save(DOSSIER / "autocollant.png", dpi=(DPI, DPI))


if __name__ == "__main__":
    qr(mm(50)).save(DOSSIER / "qr_philippe.png", dpi=(DPI, DPI))
    carte_visite()
    autocollant()
    print("Visuels créés dans", DOSSIER)
