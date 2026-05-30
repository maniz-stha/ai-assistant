from fastapi import FastAPI
from pydantic import BaseModel
from retriever import Retriever

class Query(BaseModel):
    query: str

app = FastAPI()

@app.get("/")
def root():
    return {"message": " RAG app running."}


@app.post("/chat/")
def chat(query: Query):
    user_query = query.query
    retriever = Retriever(user_query)
    response = retriever.response()
    return {"response": response}
