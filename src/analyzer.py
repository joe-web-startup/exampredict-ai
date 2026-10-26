import re
from collections import Counter, defaultdict


CONCEPTS = {
    "mouvement": [
        "mouvement",
        "mouvement rectiligne",
        "mouvement circulaire",
        "vitesse",
        "accélération",
        "trajectoire",
    ],

    "forces": [
        "force",
        "forces",
        "poids",
        "force de frottement",
        "frottement",
        "deuxième loi de newton",
        "loi de newton",
    ],

    "énergie": [
        "énergie",
        "énergie cinétique",
        "énergie potentielle",
        "énergie mécanique",
        "conservation de l'énergie",
        "travail",
        "puissance",
    ],

    "électricité": [
        "électricité",
        "courant électrique",
        "intensité",
        "tension",
        "résistance",
        "résistance électrique",
        "loi d'ohm",
        "circuit électrique",
        "condensateur",
    ],

    "ondes": [
        "onde",
        "ondes",
        "onde progressive",
        "onde mécanique",
        "onde sonore",
        "fréquence",
        "longueur d'onde",
        "célérité",
        "diffraction",
        "interférences",
    ],

    "optique": [
        "optique",
        "lentille",
        "lentilles",
        "distance focale",
        "image",
        "réfraction",
        "réflexion",
        "lumière",
        "spectre",
    ],

    "chimie": [
        "chimie",
        "réaction chimique",
        "équation chimique",
        "réactif",
        "produit",
        "quantité de matière",
        "mole",
        "masse molaire",
        "concentration",
    ],

    "acide-base": [
        "acide",
        "base",
        "acide-base",
        "ph",
        "pka",
        "solution acide",
        "solution basique",
        "titrage",
    ],

    "oxydoréduction": [
        "oxydation",
        "réduction",
        "oxydoréduction",
        "oxydant",
        "réducteur",
        "électron",
    ],

    "thermodynamique": [
        "température",
        "chaleur",
        "thermodynamique",
        "transfert thermique",
        "transfert de chaleur",
        "équilibre thermique",
    ],

    "radioactivité": [
        "radioactivité",
        "radioactif",
        "désintégration",
        "demi-vie",
        "noyau",
        "nucléaire",
    ],

    "gaz et pression": [
        "pression",
        "gaz",
        "gaz parfait",
        "volume",
        "pression atmosphérique",
    ],
}


def count_keyword(text, keyword):
    motif = r"\b" + re.escape(keyword) + r"\b"
    return len(re.findall(motif, text))


def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def find_concepts(text):
    text = clean_text(text)
    found = Counter()

    for concept, keywords in CONCEPTS.items():
        for keyword in keywords:
            occurrences = text.count(keyword)

            if occurrences > 0:
                found[concept] += occurrences

    return found


def analyze_documents(documents):
    global_counts = Counter()
    document_counts = defaultdict(int)

    for document_name, text in documents.items():
        concepts = find_concepts(text)

        for concept, count in concepts.items():
            global_counts[concept] += count
            document_counts[concept] += 1

    return global_counts, document_counts


def calculate_priorities(global_counts, document_counts, total_documents):
    results = []

    if not global_counts:
        return results

    max_frequency = max(global_counts.values())

    for topic, frequency in global_counts.items():
        documents_seen = document_counts[topic]

        frequency_score = (frequency / max_frequency) * 60
        recurrence_score = (documents_seen / total_documents) * 40

        score = round(frequency_score + recurrence_score)

        results.append({
            "topic": topic,
            "frequency": frequency,
            "documents": documents_seen,
            "score": score,
        })

    return sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )
