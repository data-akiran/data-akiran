# 🤖 LLM SQL Copilot

A full-stack AI-powered SQL assistant that allows users to query databases using natural language. Built with Groq (Llama 3.1), FastAPI, PostgreSQL, and Streamlit - all fully dockerized.

## 🚀 Features

- **Natural Language to SQL**: Ask questions in plain English, get SQL queries
- **Automatic Query Execution**: LLM generates and executes optimized SQL
- **Interactive UI**: Beautiful Streamlit interface with real-time results
- **Schema Browser**: Explore your database structure
- **Query History**: Track and revisit past queries
- **Sample Queries**: Get started quickly with pre-built examples
- **Raw SQL Mode**: Advanced users can execute custom SQL
- **Fully Dockerized**: One command to run everything

## 🛠️ Technology Stack

- **LLM API**: Groq (cloud-hosted, no local GPU required)
- **Model**: Llama 3.1 8B Instant
- **Database**: PostgreSQL 16
- **Backend API**: FastAPI
- **Frontend**: Streamlit
- **Containerization**: Docker Compose

## 📁 Project Structure

```
llm-sql-copilot/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── init-db/
│   └── 01-create-sample-data.sql
└── README.md
```

## 🏃 Quick Start

### Prerequisites

- Docker Desktop installed
- Groq API key (free at https://console.groq.com)
- At least 4GB RAM available

### Installation

1. **Clone or create the project structure**:
```bash
mkdir llm-sql-copilot
cd llm-sql-copilot
```

2. **Create the directory structure**:
```bash
mkdir -p backend frontend init-db
```

3. **Add all the files** to their respective directories

4. **Add your Groq API key** to `docker-compose.yml`:
```yaml
backend:
  environment:
    GROQ_API_KEY: your_groq_api_key_here
```

5. **Start the application**:
```bash
docker compose up -d --build
```

6. **Access the application**:
   - **Streamlit UI**: http://localhost:8501
   - **FastAPI Docs**: http://localhost:8000/docs
   - **PostgreSQL**: localhost:5432

## 📊 Sample Database

The system comes with a pre-populated e-commerce database containing:

- **Customers**: 10 sample customers
- **Products**: 15 products across multiple categories
- **Orders**: 15 orders with various statuses
- **Order Items**: Detailed order line items

### Database Schema

**Tables:**
- `customers` - Customer information
- `products` - Product catalog
- `orders` - Order headers
- `order_items` - Order line items

**Views:**
- `customer_order_summary` - Customer purchase summary
- `product_sales_summary` - Product sales statistics

## 💡 Example Queries

Try asking these questions:

- "Show me all customers from California"
- "What are the top 5 products by sales?"
- "Calculate the average order value"
- "List all orders from the last 30 days"
- "Which customer has spent the most money?"
- "Show me the monthly revenue trend"
- "What products are out of stock?"
- "List customers who haven't ordered in 6 months"

## 🔧 Configuration

### Environment Variables

**Backend** (set in `docker-compose.yml`):
```env
DATABASE_URL=postgresql://copilot:copilot123@postgres:5432/copilot
GROQ_API_KEY=your_groq_api_key_here
```

**Frontend** (set in `docker-compose.yml`):
```env
BACKEND_URL=http://backend:8000
STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
```

### Database Credentials

- **Database**: copilot
- **Username**: copilot
- **Password**: copilot123
- **Port**: 5432

### Getting a Groq API Key

1. Go to https://console.groq.com
2. Sign up for a free account
3. Navigate to API Keys → Create API Key
4. Add the key to your `docker-compose.yml`

## 📖 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /query` - Execute natural language query
- `GET /schema` - Get database schema
- `POST /execute-sql` - Execute raw SQL
- `GET /sample-queries` - Get sample queries
- `GET /health` - Health check

## 🐛 Troubleshooting

### Backend disconnected
```bash
# Check backend logs
docker compose logs backend

# Verify health
curl http://localhost:8000/health
```

### Database is empty
If tables exist but have no data, load it manually:
```bash
docker exec -i sql-copilot-db psql -U copilot -d copilot < ./init-db/01-create-sample-data.sql
```

### Database does not exist
The volume may have been created before the env vars were set:
```bash
# Wipe volume and reinitialize
docker compose down -v
docker compose up -d
```

### Streamlit file watcher deadlock (macOS)
Already handled via `STREAMLIT_SERVER_FILE_WATCHER_TYPE=none` in docker-compose.yml.

### Query timeouts
The app uses direct Groq API calls (not LangChain agents) for fast responses. If timeouts persist, increase the timeout in `frontend/app.py`:
```python
response = requests.post(..., timeout=120)
```

## 🔄 Development

### Watch logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Restart services
```bash
docker compose restart backend
docker compose restart frontend
```

### Rebuild after code changes
```bash
# Delete pycache first
rm -rf ./backend/__pycache__
docker compose up -d --build backend
```

## 📊 Monitoring

### Check service health
```bash
# Check all containers
docker compose ps

# Check resource usage
docker stats --no-stream

# Check backend health
curl http://localhost:8000/health
```

## 🛑 Stopping the Application

```bash
# Stop all services
docker compose down

# Stop and remove volumes (database data will be lost)
docker compose down -v
```

## 🚀 Scaling Up

### Use a more powerful model
Edit `backend/main.py` and change the model:
```python
model="llama-3.3-70b-versatile"  # smarter but slower
model="llama-3.1-8b-instant"     # faster, default
```

### Add more database tables
Place SQL files in `init-db/` directory. They will be executed on first startup (fresh volume only).

## 📝 License

MIT License - feel free to use for your projects!

## 🙏 Acknowledgments

- Groq for fast LLM inference API
- FastAPI for modern API development
- Streamlit for rapid UI development
- PostgreSQL for reliable data storage

---

Built with ❤️ using AI and open-source technologies