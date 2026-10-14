# Tamil Nadu Agriculture Schemes AI

An AI-powered, bilingual chatbot that helps farmers understand Tamil Nadu government agriculture schemes, subsidies, eligibility criteria, benefits, and application procedures using official source documents.

The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from indexed documents and generate evidence-based answers with source citations.

## Features

- **Bilingual chat:** Ask questions in Tamil or English.
- **Scheme information:** Find information about agricultural schemes, seed subsidies, eligibility criteria, and benefits.
- **Source-grounded answers:** Generate responses using retrieved documents instead of relying only on the language model's general knowledge.
- **Source citations:** Display available document names and page references.
- **Hallucination control:** Avoid inventing scheme details when the retrieved evidence does not support an answer.
- **Interactive chat interface:** ChatGPT-style workspace built with Streamlit.
- **REST API:** FastAPI endpoints for health checks and question answering.
- **Vector search:** Retrieve relevant document chunks using FAISS and OpenAI embeddings.
- **Regression tests:** Check key responses, source citations, and handling of unavailable information.

## Project Objectives

The project aims to make Tamil Nadu agriculture scheme information easier to access by allowing users to ask natural-language questions instead of manually searching through government documents.

The intended coverage is at least 30 agriculture schemes, subject to verification of the ingested source inventory.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| RAG framework | LangChain |
| Embedding model | OpenAI `text-embedding-3-small` |
| Language model | OpenAI `gpt-4.1-mini` |
| Vector database | FAISS |
| Backend API | FastAPI |
| Frontend | Streamlit |
| PDF processing | PyMuPDF / PDF loaders |
| Web content extraction | Requests and BeautifulSoup |
| Environment configuration | python-dotenv |

## Architecture

```text
Official Government Websites and PDFs
                  |
                  v
          Document Ingestion
                  |
                  v
       Text Extraction and Chunking
                  |
                  v
       OpenAI Embeddings Generation
                  |
                  v
             FAISS Index
                  |
                  v
         User Question (Tamil/English)
                  |
                  v
       Query Preparation and Retrieval
                  |
                  v
       Relevant Document Selection
                  |
                  v
       LLM Generates Grounded Answer
                  |
                  v
         Answer with Source Citations
                  |
                  v
             FastAPI Backend
                  |
                  v
           Streamlit Chat UI
```

## Project Structure

```text
tn-agriculture-schemes/
├── app/
│   ├── ingest.py
│   ├── rag.py
│   ├── api.py
│   ├── streamlit_app.py
│   ├── test_rag.py
│   ├── test_api.py
│   └── static/
│       └── Emblem_of_Tamil_Nadu.svg.webp
├── data/
│   ├── raw/
│   │   └── Official PDF documents
│   ├── processed/
│   └── vectorstore/
│       └── faiss_index/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

*The structure above describes the main project files. Your actual repository may contain additional files.*

## Getting Started

### 1. Prerequisites

- Python 3.12 recommended
- An OpenAI API key
- Git
- Terminal access

### 2. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd tn-agriculture-schemes
```

Replace the placeholder with your actual GitHub repository URL.

### 3. Create and activate a virtual environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
API_URL=http://127.0.0.1:8000/api/chat
```

Replace the placeholder with your own OpenAI API key.

**Security:** Never commit `.env` or expose your API key in GitHub, screenshots, or public logs.

### 6. Prepare the vector index

The application requires the FAISS index at:

```text
data/vectorstore/faiss_index/
```

If the index is not available in your local environment, place the official source documents in `data/raw/` and run the ingestion script:

```bash
python3 app/ingest.py
```

Ensure that the ingestion script is configured to save the index to the expected location.

## Running the Application

The application uses separate FastAPI and Streamlit processes.

### 1. Start the FastAPI backend

Open a terminal in the project root, activate the virtual environment, and run:

```bash
uvicorn app.api:app --reload
```

The backend should be available at:

- API base: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 2. Start the Streamlit frontend

Open another terminal in the project root and activate the virtual environment:

```bash
source .venv/bin/activate
streamlit run app/streamlit_app.py
```

Open the local URL displayed by Streamlit, usually:

`http://localhost:8501`

The frontend sends questions to the FastAPI backend and displays the generated answer with available source references.

## API Endpoints

### Health Check

**Endpoint:** `GET /health`

Checks whether the backend service is responding.

Example:

```bash
curl http://127.0.0.1:8000/health
```

### Ask a Question

**Endpoint:** `POST /api/chat`

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How much subsidy is available for certified maize seeds?"}'
```

The response includes the question, generated answer, and available source references.

Example response shape:

```json
{
  "question": "How much subsidy is available for certified maize seeds?",
  "answer": "The answer based on retrieved government documents.",
  "sources": [
    {
      "source": "tamilnadu.pdf",
      "page": 1,
      "citation": "tamilnadu.pdf, page 1"
    }
  ]
}
```

*This is an illustrative response format. Actual answer and source metadata depend on the indexed documents and API implementation.*

## Running Regression Tests

Activate the virtual environment before running the tests.

### RAG tests

```bash
python3 app/test_rag.py
```

The current regression suite covers:

- Certified maize seed subsidy amount
- Tamil seed subsidy questions and oilseeds eligibility
- Unsupported document requirements
- Missing application deadlines

The current recorded result is **4/4 regression tests passed**.

### API tests

```bash
python3 app/test_api.py
```

The API checks cover the health endpoint, selected question responses, and expected source behaviour.

Passing these tests does not guarantee that every scheme or every possible answer is accurate. The source documents and generated responses should be evaluated as coverage expands.

## Data Sources and Citations

The application uses official government agriculture scheme documents and relevant agricultural information sources that have been collected and indexed for retrieval.

The indexed source documents are stored under:

```text
data/raw/
```

The FAISS vector index is stored under:

```text
data/vectorstore/faiss_index/
```

Answers should cite available document names and page references so users can verify important information against the original source.

Information such as application deadlines, required documents, eligibility conditions, and subsidy amounts should not be inferred when the retrieved sources do not establish it.

## Limitations

- Answer quality depends on the completeness and quality of the ingested documents.
- PDF text extraction may be imperfect, particularly for Tamil-language documents with complex formatting.
- A successful retrieval does not guarantee that every answer is factually correct.
- Scheme availability, eligibility rules, and application deadlines may change.
- Users should confirm important details with the relevant official department.
- The intended coverage of 30 or more schemes must be verified against the actual indexed scheme inventory.

## Security and Responsible Use

- Keep API keys in environment variables.
- Do not commit `.env`, credentials, or other secrets.
- Do not treat generated answers as a substitute for official scheme notifications.
- Verify important eligibility and application details with the appropriate government authority.

## Future Improvements

- Expand and verify coverage of at least 30 agriculture schemes.
- Improve Tamil PDF text extraction and retrieval.
- Add more official sources and updated scheme documents.
- Improve retrieval evaluation and citation accuracy.
- Add document-level coverage reporting and additional regression tests.

## Project Status

The core RAG pipeline, FAISS retrieval, FastAPI backend, Streamlit frontend, source references, and initial regression tests have been implemented.

Final scheme coverage and source inventory should be verified before making claims about the number of fully supported schemes.

## License

Add the appropriate license before distributing the project publicly. Ensure that source documents are used and redistributed in accordance with their applicable terms.
