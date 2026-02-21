# 🤖 LLM SQL Copilot

A full-stack AI-powered SQL assistant that allows users to query databases using natural language. Built with Llama 3, LangChain, FastAPI, PostgreSQL, and Streamlit - all fully dockerized.

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

- **LLM Runtime**: Ollama
- **Model**: Llama 3 (8B parameters)
- **Agent Framework**: LangChain
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
- At least 8GB RAM available
- 10GB free disk space

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

3. **Add all the files** from the artifacts to their respective directories

4. **Start the application**:
```bash
docker-compose up -d
```

5. **Wait for Ollama to pull Llama 3** (this takes 5-10 minutes the first time):
```bash
docker-compose logs -f ollama-init
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

**Backend (`backend/.env`)**:
```env
DATABASE_URL=postgresql://copilot:copilot123@postgres:5432/sample_data
OLLAMA_URL=http://ollama:11434
```

**Frontend (`frontend/.env`)**:
```env
BACKEND_URL=http://backend:8000
```

### Database Credentials

- **Database**: sample_data
- **Username**: copilot
- **Password**: copilot123
- **Port**: 5432

## 📖 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /query` - Execute natural language query
- `GET /schema` - Get database schema
- `POST /execute-sql` - Execute raw SQL
- `GET /sample-queries` - Get sample queries
- `GET /health` - Health check

## 🐛 Troubleshooting

### Ollama not responding
```bash
# Check Ollama logs
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama
```

### Model not loading
```bash
# Check if model is pulled
docker exec sql-copilot-ollama ollama list

# Manually pull model
docker exec sql-copilot-ollama ollama pull llama3
```

### Backend connection errors
```bash
# Check backend logs
docker-compose logs backend

# Verify database is running
docker-compose ps postgres
```

### Database connection issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to database manually
docker exec -it sql-copilot-db psql -U copilot -d sample_data
```

## 🔄 Development

### Watch logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuild after code changes
```bash
docker-compose down
docker-compose up -d --build
```

## 📊 Monitoring

### Check service health
```bash
# Check all containers
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check Ollama
curl http://localhost:11434/api/tags
```

### Resource usage
```bash
docker stats
```

## 🛑 Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (database data will be lost)
docker-compose down -v
```

## 🚀 Scaling Up

### Use a more powerful model
Edit `docker-compose.yml` and change the model in `ollama-init`:
```yaml
command:
  - -c
  - |
    echo "Pulling Llama 3 70B model..."
    ollama pull llama3:70b
```

### Add more database tables
Place SQL files in `init-db/` directory. They will be executed on first startup.

### Custom LLM parameters
Modify `backend/main.py`:
```python
llm = Ollama(
    model="llama3",
    base_url=OLLAMA_URL,
    temperature=0,  # Adjust for creativity
    num_ctx=4096    # Context window size
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

MIT License - feel free to use for your projects!

## 🙏 Acknowledgments

- Ollama for LLM runtime
- LangChain for agent framework
- FastAPI for modern API development
- Streamlit for rapid UI development

## 📧 Support

For issues and questions:
- Check the troubleshooting section
- Review Docker logs
- Open an issue on GitHub

---

Built with ❤️ using AI and open-source technologies