import os
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "/tmp/chroma"
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

embedder = SentenceTransformer(EMBEDDING_MODEL)

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

def embed(texts: List[str]) -> List[List[float]]:
    return embedder.encode(texts, show_progress_bar=False).tolist()

def add_chunks(texts: List[str], metadatas: List[Dict]):
    if not texts:
        return
    embeddings = embed(texts)
    existing = collection.count()
    ids = [f"chunk_{existing}_{i}" for i in range(len(texts))]
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)

def search(query: str, top_k: int = 5):
    count = collection.count()
    if count == 0:
        return {"documents": [[]], "metadatas": [[]]}
    query_embedding = embed([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count)
    )
    return results

def get_stats():
    return {
        "total_chunks": collection.count(),
        "collection": COLLECTION_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "storage": CHROMA_DIR
    }