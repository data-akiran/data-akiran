# 🧠 Data Engineering Knowledge Copilot

A production-style Retrieval-Augmented Generation (RAG) system that answers questions from your own documents — PDFs, Markdown files, and text files. Built with FastAPI, ChromaDB, Groq (Llama 3.1), sentence-transformers, and Streamlit.

---

## 🚀 Features

- **Natural Language Q&A**: Ask questions about your documents in plain English
- **PDF, Markdown & TXT support**: Upload any of these directly via UI or API
- **Semantic Search**: Uses sentence-transformers embeddings + ChromaDB vector search
- **Fast LLM responses**: Powered by Groq's `llama-3.1-8b-instant` — no local GPU needed
- **Source attribution**: Every answer shows which document it came from
- **Chat UI**: Dark terminal-style Streamlit interface
- **Fully Dockerized**: One command to run everything

---

## 🏗 Architecture

```
User Question
     │
     ▼
Streamlit UI (port 8501)
     │
     ▼
FastAPI Backend (port 8000)
     │
     ├── ingest.py      → load + chunk documents
     ├── vector_store.py → ChromaDB embeddings + search
     ├── retriever.py   → top-k semantic search
     └── llm.py         → Groq API answer generation
```

**RAG Flow:**
1. Documents are chunked into 800-char pieces and embedded
2. Embeddings stored in ChromaDB (`/tmp/chroma` inside container)
3. User question is embedded and top-5 similar chunks retrieved
4. Chunks + question sent to Groq LLM in a single API call
5. Answer returned with source filenames

---

## 📁 Project Structure

```
de-knowledge-copilot/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py           # FastAPI endpoints
│   ├── ingest.py         # Document loading & chunking
│   ├── vector_store.py   # ChromaDB + embeddings
│   ├── retriever.py      # Semantic search
│   └── llm.py            # Groq LLM call
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py            # Streamlit chat UI
└── data/
    ├── uploads/           # Drop documents here
    └── chroma/            # Vector store (auto-created)
```

---

## 🛠️ Technology Stack

| Component | Tool |
|-----------|------|
| API | FastAPI + Uvicorn |
| Vector DB | ChromaDB >= 0.5.0 |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| LLM | Groq — `llama-3.1-8b-instant` |
| PDF parsing | PyPDF |
| Markdown parsing | Unstructured |
| Frontend | Streamlit |
| Containerization | Docker Compose |

---

## 🏃 Quick Start

### Prerequisites
- Docker Desktop installed
- Groq API key (free at https://console.groq.com)
- At least 4GB free disk space

### Setup

1. **Create project structure:**
```bash
mkdir -p de-knowledge-copilot/backend
mkdir -p de-knowledge-copilot/frontend
mkdir -p de-knowledge-copilot/data/uploads
mkdir -p de-knowledge-copilot/data/chroma
cd de-knowledge-copilot
```

2. **Copy all files** into their respective folders

3. **Add your Groq API key** to `docker-compose.yml`:
```yaml
environment:
  GROQ_API_KEY: your_key_here
```

4. **Build and run:**
```bash
docker compose up --build
```

5. **Access:**
   - Chat UI → http://localhost:8501
   - API docs → http://localhost:8000/docs

---

## 📖 API Endpoints

### `POST /ask`
Ask a question against the knowledge base.

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the net pay?", "top_k": 5}'
```

Response:
```json
{
  "question": "What is the net pay?",
  "answer": "$3,710.84",
  "sources": ["/app/data/uploads/paystub.pdf"]
}
```

### `POST /ingest/file`
Upload a PDF, Markdown, or TXT file.

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@/path/to/your/document.pdf;type=application/pdf"
```

### `POST /ingest/directory`
Ingest all supported files from a directory.

```bash
curl -X POST "http://localhost:8000/ingest/directory?path=/app/data/uploads"
```

### `GET /stats`
Get knowledge base stats.

```bash
curl http://localhost:8000/stats
```

Response:
```json
{
  "total_chunks": 42,
  "collection": "knowledge_base",
  "embedding_model": "all-MiniLM-L6-v2",
  "storage": "/tmp/chroma"
}
```

### `GET /health`
Health check.

---

## 📄 Supported File Types

| Type | Extension |
|------|-----------|
| PDF | `.pdf` |
| Markdown | `.md` |
| Plain text | `.txt` |

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | required | Your Groq API key |
| `BACKEND_URL` | `http://backend:8000` | Frontend → backend URL |
| `CHUNK_SIZE` | 800 | Characters per chunk |
| `CHUNK_OVERLAP` | 100 | Overlap between chunks |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `MODEL` | `llama-3.1-8b-instant` | Groq LLM model |

---

## ⚠️ Important Notes

### Knowledge base resets on container restart
ChromaDB is stored at `/tmp/chroma` inside the container. This means uploaded documents are lost when the container restarts. Re-upload after every restart:

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@/path/to/document.pdf;type=application/pdf"
```

To make it persistent, mount a volume to `/tmp/chroma` in `docker-compose.yml`.

### Disk space
Docker images for this project are large (~4-5GB) due to `sentence-transformers` and `chromadb`. Clean up regularly:

```bash
# Check usage
docker system df

# Free unused images and cache
docker system prune -a --volumes
```

### macOS file watcher
`STREAMLIT_SERVER_FILE_WATCHER_TYPE=none` is set in `docker-compose.yml` to prevent the macOS bind mount deadlock error.

---

## 🐛 Troubleshooting

### Backend not starting — `disk I/O error`
ChromaDB SQLite conflict on macOS. Fixed by using `/tmp/chroma` path in `vector_store.py`.

### `proxies` TypeError on startup
Old `groq` package version. Fixed by using `groq>=0.9.0` and `httpx>=0.27.0,<0.28.0` in `requirements.txt`.

### Frontend shows "Backend Disconnected"
Backend isn't running or crashed. Check:
```bash
docker compose logs backend --tail 30
curl http://localhost:8000/health
```

### Port already in use
```bash
docker compose down
docker compose up --build
```

---

## 🔄 Development

### Restart a single service
```bash
docker compose restart backend
docker compose restart frontend
```

### Rebuild after code changes
```bash
docker compose build --no-cache backend
docker compose up backend
```

### Watch logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 🛑 Stopping

```bash
docker compose down
```

---

## 🚀 What's Next (v2)

- SQL scripts ingestion
- Airflow DAG ingestion
- GitHub repo ingestion
- Persistent vector store across restarts
- Multi-collection support per project
- Re-ranking retrieved chunks

---

## 📝 License

MIT License - feel free to use for your projects!

---

Built with ❤️ using FastAPI, ChromaDB, and Groq