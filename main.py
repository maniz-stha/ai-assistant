from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from retriever import Retriever

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

app = FastAPI()
retriever = Retriever()

@app.get("/")
def root():
    return {"message": "RAG app running."}

@app.post("/chat/")
def chat(request: ChatRequest):
    response = retriever.query(request.message, session_id=request.session_id)
    return {
        "response": response,
        "session_id": request.session_id
    }
