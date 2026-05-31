from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from retriever import Retriever
from config import config
from rate_limiter import RateLimiter

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = Retriever()

limiter = RateLimiter(requests_limit=10, window_seconds=60)

@app.get("/")
def root():
    return {"message": "RAG app running."}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat")
def chat(request: ChatRequest, fastapi_req: Request):
    client_ip = fastapi_req.client.host
    
    allowed, retry_after = limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )

    response = retriever.query(request.message, session_id=request.session_id)
    return {
        "response": response,
        "session_id": request.session_id
    }
