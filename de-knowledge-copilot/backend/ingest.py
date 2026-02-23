import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from vector_store import add_chunks

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " ", ""]
)


def load_file(path: str):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(path)
    elif ext == ".md":
        loader = UnstructuredMarkdownLoader(path)
    elif ext == ".txt":
        loader = TextLoader(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()


def ingest_file(path: str) -> int:
    print(f"[ingest] Loading: {path}")
    docs = load_file(path)
    chunks = text_splitter.split_documents(docs)

    texts = [c.page_content for c in chunks]
    metadatas = [{"source": path, "chunk_id": i} for i, c in enumerate(chunks)]

    add_chunks(texts, metadatas)
    print(f"[ingest] Added {len(texts)} chunks from {path}")
    return len(texts)


def ingest_directory(directory: str) -> int:
    supported = {".pdf", ".md", ".txt"}
    total = 0
    for root, _, files in os.walk(directory):
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in supported:
                fpath = os.path.join(root, fname)
                try:
                    total += ingest_file(fpath)
                except Exception as e:
                    print(f"[ingest] Skipping {fpath}: {e}")
    return total