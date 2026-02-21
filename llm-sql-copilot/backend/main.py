from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from sqlalchemy import create_engine, text, inspect
from groq import Groq

app = FastAPI(title="SQL Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://copilot:copilot123@postgres:5432/copilot")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

engine = create_engine(DATABASE_URL)
client = Groq(api_key=GROQ_API_KEY)

def get_schema_string():
    inspector = inspect(engine)
    schema = []
    for table_name in inspector.get_table_names():
        columns = [f"{c['name']} {c['type']}" for c in inspector.get_columns(table_name)]
        schema.append(f"Table {table_name}: ({', '.join(columns)})")
    return "\n".join(schema)

def generate_sql(question: str) -> str:
    schema = get_schema_string()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"""You are a SQL expert. Given a question, return ONLY a valid PostgreSQL query with no explanation, no markdown, no backticks.
Schema:
{schema}"""},
            {"role": "user", "content": question}
        ],
        temperature=0,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    sql_query: Optional[str] = None
    result: Any
    explanation: Optional[str] = None
    error: Optional[str] = None

class SchemaResponse(BaseModel):
    tables: List[Dict[str, Any]]

@app.get("/")
def read_root():
    return {"message": "SQL Copilot API", "status": "running", "llm": "groq", "database": "connected"}

@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        groq_status = "configured" if GROQ_API_KEY else "missing"
        return {"status": "healthy", "database": "connected", "groq": groq_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/schema", response_model=SchemaResponse)
def get_schema():
    try:
        inspector = inspect(engine)
        tables = []
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({"name": column["name"], "type": str(column["type"]), "nullable": column["nullable"]})
            tables.append({"name": table_name, "columns": columns})
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schema: {str(e)}")

@app.post("/query", response_model=QueryResponse)
def execute_query(request: QueryRequest):
    try:
        sql_query = generate_sql(request.question)
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            if sql_query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = list(result.keys())
                data = [dict(zip(columns, row)) for row in rows]
                return QueryResponse(
                    question=request.question,
                    sql_query=sql_query,
                    result=data,
                    explanation="Query executed successfully"
                )
            else:
                return QueryResponse(
                    question=request.question,
                    sql_query=sql_query,
                    result="Query executed successfully",
                    explanation="Non-SELECT query executed"
                )
    except Exception as e:
        return QueryResponse(
            question=request.question,
            sql_query=None,
            result=None,
            explanation=None,
            error=str(e)
        )

@app.post("/execute-sql")
def execute_raw_sql(request: dict):
    try:
        sql = request.get("sql")
        if not sql:
            raise HTTPException(status_code=400, detail="SQL query is required")
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            if sql.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = list(result.keys())
                return {"columns": columns, "data": [dict(zip(columns, row)) for row in rows], "row_count": len(rows)}
            else:
                conn.commit()
                return {"message": "Query executed successfully", "rowcount": result.rowcount}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL execution error: {str(e)}")

@app.get("/sample-queries")
def get_sample_queries():
    return {"queries": [
        "Show me all customers from California",
        "What are the top 5 products by sales?",
        "Calculate the average order value",
        "List all orders from the last 30 days",
        "Which customer has spent the most?",
        "Show me the monthly revenue trend",
        "What products are out of stock?",
        "List customers who haven't ordered in 6 months"
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)