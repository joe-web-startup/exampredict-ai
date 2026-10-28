# WEEK 3 · DAY 4 · Faire lire un sujet d'examen PDF par une IA (Claude)
#
# Usage, depuis la racine du projet :
#   py src/lire_sujet_ia.py data/exams/2025-Metro-J1-Sujet-Original.pdf
#
# Le résultat (exercices + thèmes) est enregistré en JSON dans data/analyses/.

import base64
import json
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# La clé API est lue dans le fichier .env (jamais écrite dans le code, jamais sur GitHub)
load_dotenv()

MODELE = "claude-opus-5-5"

# La forme EXACTE de la réponse qu'on exige de l'IA (un « moule » JSON)
SCHEMA = {
    "type": "object",
    "properties": {
        "matiere": {"type": "string"},
        "annee": {"type": "integer"},
        "exercices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer"},
                    "titre": {"type": "string"},
                    "points": {"type": "number"},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "resume": {"type": "string"},
                },
                "required": ["numero", "titre", "points", "themes", "resume"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["matiere", "annee", "exercices"],
    "additionalProperties": False,
}

CONSIGNE = """Tu analyses un sujet d'examen officiel (lycée ou études supérieures).
Pour chaque exercice du sujet, donne :
- son numéro et son titre tel qu'écrit dans le sujet,
- son barème en points (0 si le sujet ne l'indique pas),
- 1 à 4 thèmes du programme, en minuscules et en français, avec des noms courts
  et réutilisables d'un sujet à l'autre (par exemple « mécanique », « ondes », « suites »),
- un résumé d'une phrase de ce qui est demandé.
Indique aussi la matière et l'année du sujet (0 si l'année n'apparaît pas)."""


def lire_pdf_en_base64(chemin):
    """Renvoie le contenu du PDF encodé en base64 (le format attendu par l'API)."""
    return base64.standard_b64encode(Path(chemin).read_bytes()).decode("utf-8")


def analyser_sujet(chemin):
    """Envoie le PDF à Claude et renvoie l'analyse sous forme de dictionnaire."""
    client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY, chargée depuis .env
    reponse = client.beta.messages.create(
        model=MODELE,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # si le modèle refuse, l'API réessaie avec un autre modèle
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": lire_pdf_en_base64(chemin),
                    },
                },
                {"type": "text", "text": CONSIGNE},
            ],
        }],
    )
    if reponse.stop_reason == "refusal":
        raise RuntimeError("L'IA a refusé d'analyser ce document.")
    texte = next(bloc.text for bloc in reponse.content if bloc.type == "text")
    usage = reponse.usage
    print(f"Tokens : {usage.input_tokens} en entrée, {usage.output_tokens} en sortie")
    return json.loads(texte)


def main():
    if len(sys.argv) < 2:
        print("Usage : py src/lire_sujet_ia.py CHEMIN_DU_PDF")
        sys.exit(1)
    chemin = Path(sys.argv[1])
    if not chemin.exists():
        print(f"Fichier introuvable : {chemin}")
        sys.exit(1)

    try:
        analyse = analyser_sujet(chemin)
    except anthropic.AuthenticationError:
        print("Clé API invalide : vérifie la ligne ANTHROPIC_API_KEY dans le fichier .env")
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("Pas de connexion à Internet.")
        sys.exit(1)
    except anthropic.APIStatusError as erreur:
        print(f"Erreur de l'API ({erreur.status_code}) : {erreur.message}")
        sys.exit(1)

    print(f"\n{analyse['matiere']} · {analyse['annee']}")
    for ex in analyse["exercices"]:
        print(f"  Exercice {ex['numero']} ({ex['points']} pts) : {ex['titre']}")
        print(f"    thèmes : {', '.join(ex['themes'])}")

    dossier = Path("data/analyses")
    dossier.mkdir(parents=True, exist_ok=True)
    sortie = dossier / (chemin.stem + ".json")
    sortie.write_text(json.dumps(analyse, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAnalyse enregistrée dans {sortie}")


if __name__ == "__main__":
    main()
