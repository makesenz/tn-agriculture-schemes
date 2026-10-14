from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.rag import ask_question

app = FastAPI(
    title="Tamil Nadu Agriculture Schemes API",
    description="RAG chatbot for Tamil Nadu agriculture schemes",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return ask_question(request.question)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer. Please try again.",
        ) from exc