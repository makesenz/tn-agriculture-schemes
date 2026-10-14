import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

RAW_DIR = Path("data/raw")
INDEX_DIR = Path("data/vectorstore/faiss_index")
PROCESSED_DIR = Path("data/processed")
WEBSITE_URL = (
    "https://agritech.tnau.ac.in/"
    "expert_system/paddy/Schemes.html"
)

def load_pdfs():
    documents = []

    for pdf_path in sorted(RAW_DIR.glob("*.pdf")):
        print(f"Loading PDF: {pdf_path.name}")

        loader = PyMuPDFLoader(str(pdf_path))
        pages = loader.load()

        for page in pages:
            page.metadata.update({
                "source": pdf_path.name,
                "source_type": "pdf",
                # PyMuPDFLoader uses zero-based page indices.
                "page_number": int(page.metadata.get("page", 0)) + 1,
            })

        documents.extend(pages)
        print(f"  Pages loaded: {len(pages)}")

    return documents


def load_website():
    print(f"Loading website: {WEBSITE_URL}")

    response = requests.get(
        WEBSITE_URL,
        timeout=30,
        headers={"User-Agent": "TN-Agriculture-Schemes-RAG/1.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup.select(
        "script, style, nav, footer, header, noscript"
    ):
        element.decompose()

    main = soup.find("main") or soup.find(id="content") or soup.body
    if main is None:
        raise ValueError("No readable page content found.")

    text = main.get_text(separator="\n", strip=True)

    if len(text) < 100:
        raise ValueError(
            "Very little webpage text extracted; inspect the page manually."
        )

    print(f"  Characters extracted: {len(text)}")

    return [
        Document(
            page_content=text,
            metadata={
                "source": WEBSITE_URL,
                "source_type": "webpage",
                "page_number": None,
            },
        )
    ]


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to your local .env file."
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    documents = load_pdfs()
    documents.extend(load_website())

    documents = [
        doc for doc in documents if doc.page_content.strip()
    ]

    if not documents:
        raise RuntimeError("No text was extracted from the sources.")

    print(f"\nDocuments/pages with text: {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)

    print(f"Chunks created: {len(chunks)}")

    # Save a small coverage report for inspection.
    source_counts = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1

    report_path = PROCESSED_DIR / "ingestion_report.txt"
    with report_path.open("w", encoding="utf-8") as report:
        report.write(f"Documents/pages with text: {len(documents)}\n")
        report.write(f"Total chunks: {len(chunks)}\n\n")
        report.write("Chunks by source:\n")
        for source, count in sorted(source_counts.items()):
            report.write(f"- {source}: {count}\n")

    print("\nCreating embeddings and FAISS index...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(str(INDEX_DIR))

    print(f"\nFAISS index saved to: {INDEX_DIR}")
    print(f"Report saved to: {report_path}")
    print("Ingestion completed successfully.")


if __name__ == "__main__":
    main()
