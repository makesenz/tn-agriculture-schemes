
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

INDEX_PATH = PROJECT_ROOT / "data" / "vectorstore" / "faiss_index"
OUTPUT_PATH = PROJECT_ROOT / "data" / "retrieval_debug.txt"

# --------------------------------------------------
# Embeddings and vector store
# --------------------------------------------------

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vectorstore = FAISS.load_local(
    str(INDEX_PATH),
    embeddings,
    allow_dangerous_deserialization=True,
)

# --------------------------------------------------
# Test questions
# --------------------------------------------------

queries = {
    "SEED_SUBSIDY": {
        "tamil": "விவசாயிகளுக்கு விதை மானியம் எவ்வளவு கிடைக்கும்?",
        "english": "What seed subsidies are available for farmers in Tamil Nadu?",
    },
    "CERTIFIED_SEEDS": {
        "tamil": "சான்றளிக்கப்பட்ட விதைகளுக்கு எவ்வளவு மானியம் கிடைக்கும்?",
        "english": "What subsidy is available for certified seeds?",
    },
    "MAIZE_SUBSIDY": {
        "tamil": "மக்காச்சோளம் விதை மானியம் எவ்வளவு?",
        "english": "What is the subsidy for certified maize seeds?",
    },
    "SEED_DOCUMENTS": {
        "tamil": "விதை மானியம் பெற தேவையான ஆவணங்கள் என்ன?",
        "english": "What documents are required to apply for seed subsidy?",
    },
    "APPLICATION_DEADLINE": {
        "tamil": "விதை மானியம் பெற விண்ணப்பிக்க கடைசி தேதி என்ன?",
        "english": "What is the application deadline for seed subsidy?",
    },
}

# --------------------------------------------------
# Direct FAISS retrieval
# --------------------------------------------------

def retrieve(query, k=5):
    return vectorstore.similarity_search_with_score(
        query,
        k=k,
    )


def format_result(rank, document, score, search_type):
    source = document.metadata.get("source", "Unknown")
    page = document.metadata.get("page_number")

    if page is None:
        page = document.metadata.get("page", "Unknown")

    return (
        f"\n--- {search_type} | Result {rank} | "
        f"Distance: {score:.4f} ---\n"
        f"Source: {source}\n"
        f"Page: {page}\n"
        f"Content:\n{document.page_content[:1500]}\n"
    )


# --------------------------------------------------
# Output collection
# --------------------------------------------------

output = []

output.append("TAMIL NADU AGRICULTURE SCHEMES - RETRIEVAL TEST")
output.append(f"FAISS index: {INDEX_PATH}")
output.append("Lower distance generally indicates a closer vector match.")
output.append(
    "Important: a close vector match does not guarantee factual relevance."
)

# --------------------------------------------------
# Test Tamil and English queries against FAISS
# --------------------------------------------------

for test_name, question in queries.items():
    output.append("\n" + "=" * 90)
    output.append(f"TEST: {test_name}")
    output.append(f"Tamil: {question['tamil']}")
    output.append(f"English: {question['english']}")
    output.append("=" * 90)

    # Tamil search
    try:
        tamil_results = retrieve(question["tamil"], k=5)

        for rank, (document, score) in enumerate(
            tamil_results,
            start=1,
        ):
            output.append(
                format_result(
                    rank,
                    document,
                    score,
                    "TAMIL FAISS SEARCH",
                )
            )

    except Exception as error:
        output.append(f"TAMIL SEARCH ERROR: {error}")

    # English search
    try:
        english_results = retrieve(question["english"], k=5)

        for rank, (document, score) in enumerate(
            english_results,
            start=1,
        ):
            output.append(
                format_result(
                    rank,
                    document,
                    score,
                    "ENGLISH FAISS SEARCH",
                )
            )

    except Exception as error:
        output.append(f"ENGLISH SEARCH ERROR: {error}")


# --------------------------------------------------
# Test actual RAG retrieval logic
# --------------------------------------------------

output.append("\n" + "#" * 90)
output.append("ACTUAL RAG RETRIEVAL TEST")
output.append("#" * 90)

try:
    from app.rag import retrieve_documents

    for test_name, question in queries.items():
        output.append("\n" + "=" * 90)
        output.append(f"RAG TEST: {test_name}")
        output.append(f"Question: {question['tamil']}")
        output.append("=" * 90)

        try:
            documents = retrieve_documents(
                question["tamil"],
                k=5,
            )

            if not documents:
                output.append("No documents returned by RAG retrieval.")

            for rank, document in enumerate(documents, start=1):
                source = document.metadata.get("source", "Unknown")
                page = document.metadata.get("page_number")

                if page is None:
                    page = document.metadata.get("page", "Unknown")

                output.append(
                    f"\n--- RAG RESULT {rank} ---\n"
                    f"Source: {source}\n"
                    f"Page: {page}\n"
                    f"Content:\n{document.page_content[:1500]}\n"
                )

        except Exception as error:
            output.append(f"RAG RETRIEVAL ERROR: {error}")

except Exception as error:
    output.append(
        "\nCould not import app.rag.retrieve_documents.\n"
        f"Error: {error}\n"
        "Direct FAISS results above are still available."
    )

# --------------------------------------------------
# Save report as UTF-8
# --------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with OUTPUT_PATH.open("w", encoding="utf-8") as file:
    file.write("\n".join(output))

print("Retrieval test completed.")
print(f"Output saved to: {OUTPUT_PATH}")
print("Open data/retrieval_debug.txt in VS Code.")
