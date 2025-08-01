import pandas as pd
import chromadb
from embedding_utils import get_embedding

client = chromadb.HttpClient(host="chromadb", port=8000)
try:
    collection = client.create_collection("movies")
except chromadb.errors.AlreadyExistsError:
    collection = client.get_collection("movies")

df = pd.read_csv("movies.csv")
for idx, row in df.iterrows():
    content = f"{row['overview']} Keywords: {row['keywords']} Genres: {row['genres']}"
    embedding = get_embedding(content)
    collection.add(
        embeddings=[embedding],
        documents=[content],
        metadatas=[{
            "title": row['title'],
            "id": row['id'],
            "overview": row['overview'],
            "genres": row['genres'],
            "keywords": row['keywords']
        }],
        ids=[str(row['id'])]
    )
    print(f"Added: {row['title']}")

print("✅ Vector DB build complete!")
