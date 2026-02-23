import streamlit as st
import requests
import os
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(
    page_title="DE Knowledge Copilot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&family=Syne:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: #0d0f12;
    color: #c9d1d9;
}

.stApp {
    background-color: #0d0f12;
}

/* Header */
.copilot-header {
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid #1e2730;
    margin-bottom: 1.5rem;
}

.copilot-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    color: #e6edf3;
    letter-spacing: -0.5px;
}

.copilot-title span { color: #39d353; }

/* Chat messages */
.msg-user {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px 10px 2px 10px;
    padding: 12px 16px;
    margin: 8px 0 8px 60px;
    font-size: 0.88rem;
    color: #c9d1d9;
    line-height: 1.6;
}

.msg-bot {
    background: #0f1923;
    border: 1px solid #1e3a4a;
    border-left: 3px solid #39d353;
    border-radius: 2px 10px 10px 10px;
    padding: 12px 16px;
    margin: 8px 60px 8px 0;
    font-size: 0.88rem;
    color: #c9d1d9;
    line-height: 1.6;
}

.msg-label {
    font-size: 0.7rem;
    font-weight: 500;
    margin-bottom: 6px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.label-user { color: #58a6ff; }
.label-bot { color: #39d353; }

.source-tag {
    display: inline-block;
    background: #1c2c1c;
    border: 1px solid #2ea04326;
    color: #39d353;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 20px;
    margin: 4px 4px 0 0;
}

.sources-row {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid #1e2730;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0a0c10 !important;
    border-right: 1px solid #1e2730;
}

section[data-testid="stSidebar"] * {
    color: #8b949e !important;
}

.sidebar-section {
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #39d353 !important;
    font-weight: 600;
    margin: 1rem 0 0.5rem 0;
}

/* Input */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #161b22 !important;
    border: 1px solid #21262d !important;
    color: #c9d1d9 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #39d353 !important;
    box-shadow: 0 0 0 1px #39d35330 !important;
}

/* Buttons */
.stButton > button {
    background: #1a2f1a !important;
    color: #39d353 !important;
    border: 1px solid #2ea04340 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: #233123 !important;
    border-color: #39d353 !important;
}

/* File uploader */
.stFileUploader > div {
    background: #161b22 !important;
    border: 1px dashed #21262d !important;
    border-radius: 8px !important;
}

/* Status pills */
.status-online {
    display: inline-block;
    width: 7px; height: 7px;
    background: #39d353;
    border-radius: 50%;
    box-shadow: 0 0 6px #39d353;
    margin-right: 6px;
    animation: blink 2s infinite;
}

.status-offline {
    display: inline-block;
    width: 7px; height: 7px;
    background: #f85149;
    border-radius: 50%;
    margin-right: 6px;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.stat-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.8rem;
}

.stat-val {
    font-size: 1.4rem;
    font-weight: 600;
    color: #39d353;
    font-family: 'Syne', sans-serif;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #3d444d;
}

.empty-icon { font-size: 3rem; margin-bottom: 12px; }
.empty-title { font-family: 'Syne', sans-serif; font-size: 1.1rem; color: #4d5566; }
.empty-sub { font-size: 0.8rem; color: #3d444d; margin-top: 6px; }

div[data-testid="stExpander"] {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "kb_stats" not in st.session_state:
    st.session_state.kb_stats = None


def check_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except:
        return False


def get_stats():
    try:
        r = requests.get(f"{BACKEND_URL}/stats", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def ask_question(question: str, top_k: int = 5):
    try:
        r = requests.post(
            f"{BACKEND_URL}/ask",
            json={"question": question, "top_k": top_k},
            timeout=30
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def upload_doc(file):
    try:
        r = requests.post(
            f"{BACKEND_URL}/ingest/file",
            files={"file": (file.name, file.getvalue(), file.type)},
            timeout=60
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ── SIDEBAR ──────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-section">⬡ System</div>', unsafe_allow_html=True)

    healthy = check_health()
    if healthy:
        st.markdown('<span class="status-online"></span> **Backend online**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline"></span> **Backend offline**', unsafe_allow_html=True)
        st.error("Cannot reach backend at " + BACKEND_URL)

    st.markdown('<div class="sidebar-section">⬡ Knowledge Base</div>', unsafe_allow_html=True)

    stats = get_stats()
    if stats:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-val">{stats.get('total_chunks', 0)}</div>
            <div>chunks indexed</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Model: `{stats.get('embedding_model', 'N/A')}`")

    st.markdown('<div class="sidebar-section">⬡ Upload Docs</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "PDF, Markdown or TXT",
        type=["pdf", "md", "txt"],
        label_visibility="collapsed"
    )

    if uploaded and st.button("➕ Ingest Document"):
        with st.spinner("Ingesting..."):
            result = upload_doc(uploaded)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(f"✓ {result.get('chunks_added', 0)} chunks added")
                st.session_state.kb_stats = None
                st.rerun()

    st.markdown('<div class="sidebar-section">⬡ Settings</div>', unsafe_allow_html=True)
    top_k = st.slider("Chunks to retrieve", min_value=1, max_value=10, value=5)

    st.divider()
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="sidebar-section">⬡ Sample Questions</div>', unsafe_allow_html=True)
    samples = [
        "What does this document cover?",
        "Summarize the key points",
        "What are the main tables or schemas?",
        "How are errors handled?",
        "What DAGs are defined?",
    ]
    for q in samples:
        if st.button(q, key=f"sample_{q}"):
            st.session_state.messages.append({"role": "user", "content": q})
            with st.spinner("Thinking..."):
                result = ask_question(q, top_k=top_k)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.get("answer", result.get("error", "No response")),
                    "sources": result.get("sources", [])
                })
            st.rerun()


# ── MAIN ─────────────────────────────────────────────
st.markdown("""
<div class="copilot-header">
    <div class="copilot-title">🧠 DE Knowledge <span>Copilot</span></div>
</div>
""", unsafe_allow_html=True)

# Chat window
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🧠</div>
            <div class="empty-title">Your knowledge base is ready</div>
            <div class="empty-sub">Upload documents in the sidebar, then ask anything about them</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <div class="msg-label label-user">▸ You</div>
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                sources_html = ""
                if msg.get("sources"):
                    tags = "".join([
                        f'<span class="source-tag">📄 {s.split("/")[-1]}</span>'
                        for s in msg["sources"]
                    ])
                    sources_html = f'<div class="sources-row"><span style="font-size:0.7rem;color:#3d444d;">SOURCES </span>{tags}</div>'

                st.markdown(f"""
                <div class="msg-bot">
                    <div class="msg-label label-bot">◈ Copilot</div>
                    {msg["content"]}
                    {sources_html}
                </div>
                """, unsafe_allow_html=True)

# Input
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([6, 1])

with col1:
    question = st.text_input(
        "Ask",
        placeholder="Ask anything about your documents...",
        label_visibility="collapsed",
        key="question_input"
    )

with col2:
    send = st.button("Send ▸", use_container_width=True)

if send and question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("Searching knowledge base..."):
        result = ask_question(question, top_k=top_k)
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("answer", result.get("error", "No response")),
            "sources": result.get("sources", [])
        })
    st.rerun()