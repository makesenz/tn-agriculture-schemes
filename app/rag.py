from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate


# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

INDEX_DIR = PROJECT_ROOT / "data" / "vectorstore" / "faiss_index"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vectorstore = FAISS.load_local(
    str(INDEX_DIR),
    embeddings,
    allow_dangerous_deserialization=True,
)

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)


# =========================================================
# QUERY EXPANSION
# =========================================================

query_prompt = ChatPromptTemplate.from_template("""
You are a search-query translator for a Tamil Nadu
agriculture government schemes knowledge base.

Convert the user's question into ONE concise English
search query that will help retrieve relevant documents.

Rules:
1. Preserve the exact intent of the question.
2. Preserve crop names, scheme names, subsidy terms,
   percentages, amounts, and technical terms.
3. Do not answer the question.
4. Do not add facts or assumptions.
5. If the question is already in English, return a
   concise search query with the same meaning.
6. If the question is in Tamil or Thanglish, translate
   its meaning into English.
7. Return ONLY the search query, without explanations.

User question:
{question}

English search query:
""")


def create_search_query(question: str) -> str:
    """Create an English retrieval query from any input language."""

    try:
        messages = query_prompt.format_messages(
            question=question
        )

        response = llm.invoke(messages)
        search_query = response.content.strip()

        # Avoid using an empty generated query.
        if not search_query:
            return question

        # Prevent excessively long search queries.
        return search_query[:500]

    except Exception as exc:
        print(f"Query expansion warning: {exc}")
        print("Falling back to the original question.")
        return question


# =========================================================
# IMPROVED RETRIEVAL
# =========================================================

import json
import re


def retrieve_documents(question: str, k: int = 5):
    """
    Retrieve English-query results first, then use the LLM
    to filter chunks that do not answer the user's question.

    Returns only relevant source documents.
    """

    english_query = create_search_query(question)

    print(f"\nOriginal query: {question}")
    print(f"English search query: {english_query}")

    # English retrieval is the primary path because Tamil PDF
    # extraction is unreliable in some of the indexed documents.
    results = vectorstore.similarity_search_with_score(
        english_query,
        k=min(max(k * 3, 10), 20),
    )

    if not results:
        print("No documents retrieved.")
        return []

    # Keep document IDs stable for relevance filtering.
    candidates = []

    for idx, (doc, score) in enumerate(results):
        source, page = get_source_and_page(doc)

        candidates.append({
            "id": idx,
            "doc": doc,
            "distance": float(score),
            "source": source,
            "page": page,
        })

    # Ask the model to identify evidence relevant to the
    # original question, not merely documents about agriculture.
    candidate_text = "\n\n".join(
        (
            f"DOCUMENT ID: {item['id']}\n"
            f"SOURCE: {item['source']}\n"
            f"PAGE: {item['page']}\n"
            f"CONTENT:\n{item['doc'].page_content[:1800]}"
        )
        for item in candidates
    )

    relevance_prompt = ChatPromptTemplate.from_template("""
You are a strict evidence selector for a Tamil Nadu
agriculture government schemes assistant.

USER QUESTION:
{question}

ENGLISH SEARCH QUERY:
{english_query}

CANDIDATE DOCUMENTS:
{documents}

Your task is to select documents that directly support
the exact information requested.

STRICT RULES:

1. Identify the specific crop, scheme, benefit, or procedure
   requested by the user.

2. A document mentioning agriculture or subsidies generally
   is NOT sufficient evidence for a specific scheme.

3. For questions about required documents, select a document
   only if it explicitly connects those documents to the
   specific scheme asked about.

4. General instructions such as Aadhaar, land proof, soil
   test reports, bank passbooks, and receipts must NOT be
   presented as mandatory for a specific scheme unless the
   source explicitly establishes that connection.

5. Do not combine information from different crops or schemes
   just because they share a subsidy percentage.

6. For deadline questions, require explicit evidence of the
   application deadline for the relevant scheme.

7. Prefer official scheme-specific information over general
   policy notes or unrelated scheme descriptions.

8. If a document is only partially relevant, do not select it
   unless it directly supports the requested answer.

9. If no candidate provides direct evidence, return an empty
   list.

Return ONLY valid JSON:
{{"relevant_ids": [0, 2]}}
""")

    try:
        response = llm.invoke(
            relevance_prompt.format_messages(
                question=question,
                english_query=english_query,
                documents=candidate_text,
            )
        )

        raw_output = response.content.strip()

        # Handle accidental Markdown code fences.
        raw_output = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw_output,
            flags=re.IGNORECASE,
        )

        parsed = json.loads(raw_output)
        relevant_ids = parsed.get("relevant_ids", [])

        if not isinstance(relevant_ids, list):
            raise ValueError("relevant_ids must be a list")

        valid_ids = {
            item["id"]
            for item in candidates
        }

        relevant_ids = [
            doc_id
            for doc_id in relevant_ids
            if isinstance(doc_id, int) and doc_id in valid_ids
        ]

        selected = [
            item["doc"]
            for item in candidates
            if item["id"] in relevant_ids
        ]

        print(f"Retrieved candidates: {len(candidates)}")
        print(f"Relevant documents selected: {len(selected)}")

        return selected[:k]

    except Exception as exc:
        # Fail closed: do not pass potentially irrelevant
        # chunks to the answer-generation model.
        print(f"Relevance filtering failed: {exc}")
        print("Returning no documents to avoid unsupported answers.")
        return []

# =========================================================
# ANSWER PROMPT
# =========================================================

prompt = ChatPromptTemplate.from_template("""
You are a reliable Tamil Nadu Agriculture Schemes assistant.

CORE RULES:
1. Answer using ONLY the retrieved source context.
2. Never invent subsidy amounts, percentages, eligibility,
   deadlines, documents, application procedures, or benefits.
3. Answer in the same language as the user's question:
   Tamil, English, or Tanglish.
4. Preserve official scheme names and technical terms when useful.
5. Use clear, natural Tamil. Avoid literal or incorrect translations.
6. If the context does not contain enough evidence, clearly say so.
7. If sources conflict, explain the conflict instead of guessing.

AGRICULTURE TERMINOLOGY:
- Maize = மக்காச்சோளம்
- Oilseeds = எண்ணெய் வித்துக்கள்
- Certified seeds = சான்றளிக்கப்பட்ட விதைகள்
- Seed subsidy = விதை மானியம்
- Small and marginal farmers = சிறு மற்றும் குறு விவசாயிகள்
- SC/ST = SC/ST (பட்டியல் சாதிகள் / பட்டியல் பழங்குடியினர்)

SUBSIDY ACCURACY:
- Do not apply a subsidy rate for one crop to another crop.
- Distinguish subsidy percentages from maximum monetary limits.
- Explain "whichever is lower" accurately when the source says so.
- Do not interpret reservation or allocation percentages as
  additional subsidy percentages.
- Mention eligibility or priority categories only when supported
  by the retrieved context.


OILSEEDS ELIGIBILITY ACCURACY:
- Preserve the complete source condition: eligible farmers must produce
  and supply Foundation and certified-class seeds to the department.
- Do not change this to merely supplying seeds produced by someone else.
- In Tamil, express this as:
  "Foundation மற்றும் சான்றளிக்கப்பட்ட வகை விதைகளை உற்பத்தி செய்து
  துறைக்கு வழங்கும் விவசாயிகள் தகுதி பெறுவர்."
- Translate technical terms naturally, but never weaken or alter
  eligibility conditions.


CROP-SPECIFIC ELIGIBILITY:
- Treat maize and oilseeds as separate schemes, even when
  their subsidy rates are identical.
- State eligibility conditions only for the corresponding crop.
- For oilseeds, preserve the full condition:
  farmers must produce and supply Foundation and certified-class
  seeds to the department to be eligible.
- Do not transfer maize's priority categories to oilseeds,
  or oilseeds' eligibility conditions to maize.
- When answering in Tamil, preserve these distinctions clearly.
- Do not simplify an eligibility condition in a way that
  changes its meaning.

SCHEME SEPARATION:
- Never merge benefits from different schemes into one subsidy.
- Identify the exact scheme associated with each subsidy amount.
- If multiple schemes match the question, explain them separately
  with their respective source citations.
- Do not imply that a scheme is available statewide when the
  retrieved source specifies only certain districts.
- If scheme identity or applicability is unclear, state that
  limitation instead of assuming both schemes apply.
- Never add a second scheme's benefit unless it directly helps
  answer the user's question.

CITATIONS:
- Cite each factual claim using the exact source filename and page.
- Put citations next to the claims they support.
- Do not cite a source for a claim it does not establish.
- Never invent filenames or page numbers.
- If the evidence is incomplete, state the limitation.

CONTEXT:
{context}

USER QUESTION:
{question}

Write a concise, accurate answer:
""")


# =========================================================
# CITATION HELPERS
# =========================================================

def get_source_and_page(doc):
    source = str(
        doc.metadata.get("source", "Unknown source")
    )

    # Prefer explicit page_number metadata if present.
    page = doc.metadata.get("page_number")

    if page is None:
        raw_page = doc.metadata.get("page")

        if raw_page is not None:
            try:
                # LangChain PDF loaders commonly use
                # zero-based page metadata.
                page = int(raw_page) + 1
            except (TypeError, ValueError):
                page = raw_page

    return source, page


# =========================================================
# MAIN RAG FUNCTION
# =========================================================

def ask_question(question: str) -> dict:
    question = question.strip()

    if not question:
        return {
            "question": question,
            "answer": "Please enter a question.",
            "sources": [],
        }

    # Retrieve using original + English search queries.
    docs = retrieve_documents(question, k=5)

    context_parts = []
    sources = []
    seen_sources = set()

    for doc in docs:
        source, page = get_source_and_page(doc)

        citation = (
            f"{source}, page {page}"
            if page is not None
            else source
        )

        context_parts.append(
            f"[Source: {citation}]\n"
            f"{doc.page_content}"
        )

        # Deduplicate displayed source references.
        source_key = (source, str(page))

        if source_key not in seen_sources:
            sources.append({
                "source": source,
                "page": page,
                "citation": citation,
            })
            seen_sources.add(source_key)

    context = "\n\n---\n\n".join(context_parts)

    messages = prompt.format_messages(
        context=context,
        question=question,
    )

    response = llm.invoke(messages)

    return {
        "question": question,
        "answer": response.content,
        "sources": sources,
    }


# =========================================================
# COMMAND-LINE TEST
# =========================================================

if __name__ == "__main__":
    question = input(
        "Ask about Tamil Nadu agriculture schemes: "
    )

    result = ask_question(question)

    print("\nANSWER\n")
    print(result["answer"])

    print("\nRETRIEVED SOURCES\n")

    for source in result["sources"]:
        print(f"- {source['citation']}")