import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Page config
st.set_page_config(
    page_title="SQL Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .sql-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
        font-family: monospace;
        margin: 1rem 0;
    }
    .result-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

def check_backend_health():
    """Check if backend is healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_schema():
    """Fetch database schema"""
    try:
        response = requests.get(f"{BACKEND_URL}/schema", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching schema: {str(e)}")
        return None

def execute_query(question):
    """Execute natural language query"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": question},
            timeout=120
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_sample_queries():
    """Get sample queries"""
    try:
        response = requests.get(f"{BACKEND_URL}/sample-queries", timeout=5)
        if response.status_code == 200:
            return response.json().get("queries", [])
        return []
    except:
        return []

# Header
st.title("🤖 SQL Copilot")
st.markdown("### Ask questions about your data in natural language")

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Health check
    health = check_backend_health()
    if health:
        st.success("✅ Backend Connected")
    else:
        st.error("❌ Backend Disconnected")
        st.stop()
    
    st.divider()
    
    # Database Schema
    st.header("📊 Database Schema")
    schema = get_schema()
    
    if schema and "tables" in schema:
        for table in schema["tables"]:
            with st.expander(f"📋 {table['name']}"):
                for col in table["columns"]:
                    st.text(f"• {col['name']} ({col['type']})")
    else:
        st.warning("No schema available")
    
    st.divider()
    
    # Sample Queries
    st.header("💡 Sample Queries")
    sample_queries = get_sample_queries()
    
    if sample_queries:
        selected_sample = st.selectbox(
            "Try a sample query:",
            [""] + sample_queries,
            key="sample_query_selector"
        )
        if selected_sample and st.button("Use This Query"):
            st.session_state.query_input = selected_sample
    
    st.divider()
    
    # Query History
    st.header("📜 History")
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
    
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            with st.expander(f"{item['timestamp'][:19]}"):
                st.caption(item['question'])

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    # Query input
    query = st.text_input(
        "Ask a question about your data:",
        value=st.session_state.get("query_input", ""),
        placeholder="e.g., Show me the top 10 customers by revenue",
        key="main_query_input"
    )

with col2:
    st.write("")  # Spacing
    execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)

# Execute query
if execute_button and query:
    with st.spinner("🔄 Processing your question..."):
        result = execute_query(query)
        
        # Add to history
        st.session_state.history.append({
            "timestamp": datetime.now().isoformat(),
            "question": query,
            "result": result
        })
        
        # Display results
        if "error" in result and result["error"]:
            st.markdown(f"""
                <div class="error-box">
                    <strong>❌ Error:</strong><br>
                    {result['error']}
                </div>
            """, unsafe_allow_html=True)
        else:
            # Display SQL query if available
            if result.get("sql_query"):
                st.markdown("#### 📝 Generated SQL Query")
                st.code(result["sql_query"], language="sql")
            
            # Display result
            st.markdown("#### 📊 Result")
            
            result_data = result.get("result", "")
            
            # Try to parse as table data
            if isinstance(result_data, str) and result_data:
                st.markdown(f"""
                    <div class="result-box">
                        {result_data}
                    </div>
                """, unsafe_allow_html=True)
            elif isinstance(result_data, list):
                # Display as dataframe
                df = pd.DataFrame(result_data)
                st.dataframe(df, use_container_width=True)
                
                # Show summary stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
            else:
                st.info(str(result_data))

# Tabs for additional features
tabs = st.tabs(["📈 Query History", "💻 Raw SQL", "ℹ️ About"])

with tabs[0]:
    st.header("Query History")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Query {len(st.session_state.history) - i}: {item['question'][:50]}..."):
                st.text(f"Timestamp: {item['timestamp']}")
                st.text(f"Question: {item['question']}")
                if item['result'].get('sql_query'):
                    st.code(item['result']['sql_query'], language="sql")
                st.json(item['result'])
    else:
        st.info("No queries executed yet")

with tabs[1]:
    st.header("Execute Raw SQL")
    st.warning("⚠️ Advanced users only. Be careful with UPDATE/DELETE queries.")
    
    raw_sql = st.text_area("Enter SQL query:", height=150)
    if st.button("Execute Raw SQL"):
        if raw_sql:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/execute-sql",
                    json={"sql": raw_sql},
                    timeout=30
                )
                result = response.json()
                
                if "error" in result:
                    st.error(result["error"])
                elif "data" in result:
                    df = pd.DataFrame(result["data"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.success(result.get("message", "Query executed successfully"))
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tabs[2]:
    st.header("About SQL Copilot")
    st.markdown("""
    ### 🚀 Features
    - **Natural Language Queries**: Ask questions in plain English
    - **Automatic SQL Generation**: LLM generates optimized SQL queries
    - **Query History**: Track your past queries
    - **Schema Browser**: Explore your database structure
    - **Sample Queries**: Get started with pre-built examples
    
    ### 🛠️ Technology Stack
    - **LLM**: Llama 3 via Ollama
    - **Agent Framework**: LangChain
    - **Database**: PostgreSQL
    - **Backend**: FastAPI
    - **Frontend**: Streamlit
    - **Deployment**: Docker Compose
    
    ### 📖 How to Use
    1. Browse the database schema in the sidebar
    2. Type your question in natural language
    3. Click "Execute Query"
    4. View the generated SQL and results
    5. Explore query history and try sample queries
    
    ### 💡 Example Questions
    - "Show me the top 10 customers by total purchases"
    - "What's the average order value by month?"
    - "List all products that are low on stock"
    - "Which sales rep has the highest revenue?"
    """)

# Footer
st.divider()
st.caption("Powered by Llama 3 🦙 | Built with LangChain ⛓️ | Made with Streamlit 🎈")