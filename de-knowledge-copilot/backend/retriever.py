from typing import Tuple, List
from vector_store import search, get_stats as vs_stats


def retrieve(query: str, top_k: int = 5) -> Tuple[List[str], List[str]]:
    results = search(query, top_k=top_k)
    chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    sources = [m.get("source", "unknown") for m in metadatas]
    return chunks, sources


def get_stats():
    return vs_stats()