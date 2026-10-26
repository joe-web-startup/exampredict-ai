from document_loader import load_documents
from analyzer import analyze_documents, calculate_priorities


EXAMS_FOLDER = "data/exams"


def display_results(results, total_documents):
    print("\n" + "=" * 60)
    print("                 EXAMPREDICT AI")
    print("=" * 60)

    print(f"\nDocuments analysés : {total_documents}")

    if not results:
        print("\nAucun contenu exploitable trouvé.")
        return

    print("\nTOP SUJETS À RÉVISER")
    print("-" * 60)

    for position, result in enumerate(results[:20], start=1):

        topic = result["topic"]
        score = result["score"]
        frequency = result["frequency"]
        documents = result["documents"]

        if score >= 80:
            priority = "HIGH"
        elif score >= 50:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        print(
            f"{position:2}. {topic:<20} "
            f"{score:>3}/100 | "
            f"{documents}/{total_documents} examens | "
            f"{frequency} occurrences | "
            f"{priority}"
        )

    print("\n" + "=" * 60)
    print("Analyse basée sur la récurrence historique.")
    print("Ce résultat ne garantit pas les questions du prochain examen.")
    print("=" * 60 + "\n")


def main():
    documents = load_documents(EXAMS_FOLDER)

    if not documents:
        print("\nAucun PDF ou TXT trouvé dans :")
        print(EXAMS_FOLDER)
        print("\nAjoute tes examens puis relance le programme.")
        return

    global_counts, document_counts = analyze_documents(documents)

    results = calculate_priorities(
        global_counts,
        document_counts,
        len(documents)
    )

    display_results(results, len(documents))


if __name__ == "__main__":
    main()
