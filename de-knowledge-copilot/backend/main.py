from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from pathlib import Path

from ingest import ingest_file, ingest_directory
from retriever import retrieve
from llm import generate_answer

app = FastAPI(title="Data Engineering Knowledge Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/app/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]


@app.get("/")
def root():
    return {"message": "Data Engineering Knowledge Copilot", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ask", response_model=QuestionResponse)
def ask(request: QuestionRequest):
    try:
        chunks, sources = retrieve(request.question, top_k=request.top_k)
        if not chunks:
            return QuestionResponse(
                question=request.question,
                answer="I couldn't find any relevant information in the knowledge base. Please upload some documents first.",
                sources=[]
            )
        answer = generate_answer(request.question, chunks)
        return QuestionResponse(
            question=request.question,
            answer=answer,
            sources=list(set(sources))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/file")
async def upload_file(file: UploadFile = File(...)):
    try:
        allowed = {".pdf", ".md", ".txt"}
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {allowed}")

        dest = UPLOAD_DIR / file.filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        count = ingest_file(str(dest))
        return {"message": f"Ingested {file.filename}", "chunks_added": count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/directory")
def ingest_dir(path: str):
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail=f"Directory not found: {path}")
        count = ingest_directory(path)
        return {"message": f"Ingested directory: {path}", "chunks_added": count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    from retriever import get_stats
    return get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)