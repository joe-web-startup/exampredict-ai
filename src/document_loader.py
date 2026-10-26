from pathlib import Path
from pypdf import PdfReader


def read_pdf(path):
    reader = PdfReader(path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def read_text_file(path):
    return Path(path).read_text(encoding="utf-8")


def load_documents(folder):
    folder = Path(folder)
    documents = {}

    for path in sorted(folder.iterdir()):

        if path.suffix.lower() == ".pdf":
            text = read_pdf(path)

        elif path.suffix.lower() == ".txt":
            text = read_text_file(path)

        else:
            continue

        if text.strip():
            documents[path.name] = text

    return documents
