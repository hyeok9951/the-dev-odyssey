from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from embedding_utils import get_embedding

client = chromadb.HttpClient(host="chromadb", port=8000)
collection = client.get_collection("movies")

app = FastAPI()

class RecommendRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/recommend")
def recommend_movies(req: RecommendRequest):
    query_embedding = get_embedding(req.query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=req.top_k
    )
    recs = []
    for meta in results['metadatas'][0]:
        recs.append({
            "title": meta['title'],
            "overview": meta['overview'],
            "genres": meta['genres'],
            "keywords": meta['keywords']
        })
    return {"recommendations": recs}

@app.get("/")
def root():
    return {"status": "ok"}
