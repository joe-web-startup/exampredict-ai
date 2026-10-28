# Teste chaque clé API rangée dans le fichier .env et dit laquelle fonctionne.
# Dans .env, mets une clé par ligne, avec des noms différents :
#   ANTHROPIC_API_KEY_1=sk-ant-...
#   ANTHROPIC_API_KEY_2=sk-ant-...
# Lance depuis la racine du projet :  py src/verifier_cles.py
# Coût : une réponse d'un seul token par clé (moins d'un centime au total).

from dotenv import dotenv_values
import anthropic

cles = {nom: valeur for nom, valeur in dotenv_values(".env").items()
        if nom.startswith("ANTHROPIC_API_KEY") and valeur}

if not cles:
    print("Aucune clé trouvée dans .env (les noms doivent commencer par ANTHROPIC_API_KEY).")

for nom, cle in cles.items():
    masque = cle[:10] + "..." + cle[-4:]          # on n'affiche jamais la clé entière
    client = anthropic.Anthropic(api_key=cle, max_retries=0)
    try:
        client.messages.create(
            model="claude-opus-5-5",
            max_tokens=1,
            messages=[{"role": "user", "content": "OK"}],
        )
        print(f"✅ {nom} ({masque}) : fonctionne, il y a du crédit")
    except anthropic.AuthenticationError:
        print(f"❌ {nom} ({masque}) : clé invalide ou supprimée")
    except anthropic.BadRequestError as erreur:
        if "credit" in str(erreur).lower():
            print(f"💸 {nom} ({masque}) : clé valide, mais compte SANS crédit")
        else:
            print(f"⚠️ {nom} ({masque}) : erreur de requête : {erreur.message}")
    except anthropic.PermissionDeniedError:
        print(f"⛔ {nom} ({masque}) : clé sans permission")
    except anthropic.APIStatusError as erreur:
        print(f"⚠️ {nom} ({masque}) : erreur {erreur.status_code} : {erreur.message}")
    except anthropic.APIConnectionError:
        print("Pas de connexion à Internet.")
        break
