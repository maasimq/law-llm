"""
Law LLM — Pakistani Legal Assistant
Institutional Legal Reference Design
====================================
"""

import sys
import os
import time
import html
from pathlib import Path
import re
import json
import uuid
import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import run_rag_pipeline

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Law LLM — Pakistani Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load external stylesheet
# ---------------------------------------------------------------------------
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS & ASSETS
# ============================================================

SECTION_MARK_SVG = '''<svg class="section-mark-svg" viewBox="0 0 100 100" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M54.8,24.6 C54.8,20.2 51.5,17 46.5,17 C41.2,17 37.5,20.8 37.2,26.2 L28,26.2 C28.5,15.6 36.2,8.5 46.7,8.5 C57.3,8.5 64.2,15.3 64.2,24.3 C64.2,32.2 58.7,37.3 50.8,39.6 L46.2,40.9 C41.5,42.2 38.3,45 38.3,49.2 C38.3,53.8 41.8,57.2 47,57.2 C52.7,57.2 56.6,53.2 57,47.5 L66.2,47.5 C65.7,58.3 57.8,65.7 46.8,65.7 C36.2,65.7 29,58.7 29,49.3 C29,41.2 34.7,36 42.5,33.7 L47.2,32.4 C52.2,31 54.8,28.4 54.8,24.6 Z M46.5,65.7 C57.3,65.7 64.2,72.7 64.2,81.7 C64.2,89.7 57.5,95.5 46.7,95.5 C36.2,95.5 28.5,88.4 28,77.8 L37.2,77.8 C37.5,83.2 41.2,87 46.5,87 C51.5,87 54.8,83.8 54.8,79.4 C54.8,75.6 52.2,73 47.2,71.6 L42.5,70.3 C34.7,68 29,62.8 29,54.7 C29,45.3 36.2,38.3 46.8,38.3 C57.8,38.3 65.7,45.7 66.2,56.5 L57,56.5 C56.6,50.8 52.7,46.8 47,46.8 C41.8,46.8 38.3,50.2 38.3,54.8 C38.3,59 41.5,61.8 46.2,63.1 L50.8,64.4 Z"/></svg>'''

def extract_citation_badge(chunk_text: str) -> tuple[str, str]:
    """
    Extract exact citation badge (e.g. 'CrPC § 497', 'PPC § 302', 'Art. 10')
    and document title from structured chunk headers or text.
    """
    lines = [line.strip() for line in chunk_text.split('\n') if line.strip()]
    
    act_header = None
    sec_header = None
    
    for line in lines[:6]:
        if line.startswith("ACT:"):
            act_header = line.replace("ACT:", "").strip()
        elif line.startswith("SECTION:") or line.startswith("SECTION/ARTICLE:"):
            sec_header = line.split(":", 1)[1].strip()
        elif line.startswith("ARTICLE:"):
            sec_header = line.split(":", 1)[1].strip()

    if act_header:
        act_lower = act_header.lower()
        if "criminal procedure" in act_lower or "crpc" in act_lower:
            badge = f"CrPC § {sec_header}" if sec_header else "CrPC"
            return badge, "Code of Criminal Procedure, 1898"
        elif "penal code" in act_lower or "ppc" in act_lower:
            badge = f"PPC § {sec_header}" if sec_header else "PPC"
            return badge, "Pakistan Penal Code, 1860"
        elif "constitution" in act_lower:
            badge = f"Art. {sec_header}" if sec_header else "Constitution"
            return badge, "Constitution of Pakistan"

    # Fallback for chunks without explicit ACT: headers
    text_lower = chunk_text.lower()
    if "code of criminal procedure" in text_lower or "crpc" in text_lower:
        match = re.search(r'section\s*:\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE) or re.search(r'section\s+(\d+[a-z]?)', chunk_text, re.IGNORECASE)
        badge = f"CrPC § {match.group(1).upper()}" if match else "CrPC"
        return badge, "Code of Criminal Procedure, 1898"
    elif "pakistan penal code" in text_lower or "ppc" in text_lower:
        match = re.search(r'section\s*:\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE) or re.search(r'section\s+(\d+[a-z]?)', chunk_text, re.IGNORECASE)
        badge = f"PPC § {match.group(1).upper()}" if match else "PPC"
        return badge, "Pakistan Penal Code, 1860"
    elif "constitution" in text_lower or re.search(r'^(\d+[A-Za-z]?)\.\s', chunk_text):
        match = re.search(r'^(\d+[A-Za-z]?)\.\s', chunk_text) or re.search(r'article\s+(\d+[a-z]?)', chunk_text, re.IGNORECASE)
        badge = f"Art. {match.group(1).upper()}" if match else "Constitution"
        return badge, "Constitution of Pakistan"

    return "Statute", "Legal Reference Text"


def get_history_dir() -> Path:
    """Get the local directory for saving chat history."""
    history_dir = PROJECT_ROOT / "chat_history"
    history_dir.mkdir(exist_ok=True)
    return history_dir

def load_all_sessions() -> list[dict]:
    """Load metadata for all saved chat sessions."""
    history_dir = get_history_dir()
    sessions = []
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "title": data.get("title", "Untitled Chat"),
                    "created_at": data.get("created_at", ""),
                    "filepath": filepath
                })
        except Exception:
            pass
    # Sort by created_at descending (newest first)
    sessions.sort(key=lambda x: x["created_at"], reverse=True)
    return sessions

def load_session(session_id: str):
    """Load a specific chat session into Streamlit state."""
    history_dir = get_history_dir()
    filepath = history_dir / f"{session_id}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.session_id = session_id
            st.session_state.messages = data.get("messages", [])
            st.session_state.session_title = data.get("title", "Untitled Chat")
            st.rerun()

def save_session():
    """Save the current chat session to a JSON file."""
    if not st.session_state.messages:
        return
        
    # Auto-generate title from first user message if missing
    if not st.session_state.session_title:
        first_user_msg = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "New Conversation")
        st.session_state.session_title = first_user_msg[:40] + ("..." if len(first_user_msg) > 40 else "")
        
    history_dir = get_history_dir()
    filepath = history_dir / f"{st.session_state.session_id}.json"
    
    data = {
        "id": st.session_state.session_id,
        "title": st.session_state.session_title,
        "created_at": st.session_state.created_at,
        "messages": st.session_state.messages
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def start_new_session():
    """Initialize a brand new chat session."""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.session_title = ""
    st.session_state.created_at = datetime.datetime.now().isoformat()
    st.rerun()

def delete_session(session_id: str):
    """Delete a saved chat session."""
    history_dir = get_history_dir()
    filepath = history_dir / f"{session_id}.json"
    if filepath.exists():
        filepath.unlink()
    if st.session_state.get("session_id") == session_id:
        start_new_session()
    else:
        st.rerun()


def render_sidebar():
    """Render the minimal, professional sidebar."""
    with st.sidebar:
        # Branding with Section Mark Motif SVG
        st.markdown(
            f"""
            <div class="sidebar-logo">
                <span class="sidebar-logo-icon">{SECTION_MARK_SVG}</span>
                <div>
                    <h2>Law LLM</h2>
                    <p>Pakistani Legal Assistant</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Multi-chat New Button
        if st.button("➕ New Chat", use_container_width=True):
            start_new_session()
            
        st.markdown('<hr style="margin: 1.5rem 0 1rem; border-color: rgba(255,255,255,0.06)">', unsafe_allow_html=True)

        # Chat History List
        st.markdown('<div class="sidebar-section">Recent Chats</div>', unsafe_allow_html=True)
        sessions = load_all_sessions()
        
        if not sessions:
            st.markdown('<div style="opacity: 0.5; font-size: 0.85rem; padding: 0.5rem 0;">No saved chats yet.</div>', unsafe_allow_html=True)
        else:
            for s in sessions:
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    is_active = (s["id"] == st.session_state.get("session_id"))
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(f"💬 {s['title']}", key=f"load_{s['id']}", help=s['created_at'], use_container_width=True):
                        load_session(s["id"])
                with col2:
                    if st.button("🗑️", key=f"del_{s['id']}", help="Delete chat"):
                        delete_session(s["id"])

        st.markdown('<hr style="margin: 1.5rem 0 1rem; border-color: rgba(255,255,255,0.06)">', unsafe_allow_html=True)

        # Sources
        st.markdown('<div class="sidebar-section">Legal Authorities</div>', unsafe_allow_html=True)
        sources = ["Pakistan Penal Code, 1860", "Constitution of Pakistan", "Code of Criminal Procedure, 1898"]
        for src in sources:
            st.markdown(
                f"""
                <div class="source-item">
                    <span class="source-dot">■</span> {src}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('<hr style="margin: 1.5rem 0 1rem; border-color: rgba(255,255,255,0.06)">', unsafe_allow_html=True)

        # Quiet Disclaimer
        st.markdown(
            """
            <div class="sidebar-disclaimer">
                <strong>Informational Use Only</strong>
                This assistant provides statutory reference information. It does not constitute formal legal advice.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state():
    """Render the quiet, professional legal hero screen."""
    st.markdown(
        f"""
        <div class="hero-section">
            <div class="hero-section-mark-container">{SECTION_MARK_SVG}</div>
            <div class="hero-title">Pakistani Legal Assistant</div>
            <p class="hero-subtitle">Search statutory law and constitutional provisions with exact section citations.<br>
            <span style="opacity: 0.8; font-family: 'Noto Nastaliq Urdu', serif;">(آپ قانون کے متعلق سوالات اردو میں بھی پوچھ سکتے ہیں)</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown('<div class="suggestions-label">Popular Topics</div>', unsafe_allow_html=True)
    
    # Main-panel popular questions pills
    pills = ["Bail", "FIR", "Theft", "Murder", "Fundamental Rights"]
    cols = st.columns(len(pills))
    for col, pill in zip(cols, pills):
        with col:
            if st.button(pill, key=f"pill_{pill}", use_container_width=True):
                st.session_state.pending_question = pill


def clean_statutory_text(raw_text: str) -> str:
    """Clean raw PDF extraction artifacts from statutory source text."""
    lines = raw_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Skip header metadata lines
        if (stripped.startswith("ACT:") or 
            stripped.startswith("SECTION:") or 
            stripped.startswith("SECTION/ARTICLE:") or 
            stripped.startswith("ARTICLE:") or 
            stripped.startswith("TITLE:") or 
            stripped.startswith("CHAPTER:")):
            continue
        # Skip divider lines
        if re.match(r'^={3,}$', stripped) or re.match(r'^-{3,}$', stripped):
            continue
        # Skip page number artifacts
        if re.search(r'Page\s+\d+\s+of\s+\d+', stripped, re.IGNORECASE) or re.search(r'^\s*Page\s+\d+\s*$', stripped, re.IGNORECASE):
            continue
        # Skip footnote annotations e.g. "1 Subs. by...", "1 Ins., ibid.", "1* * *"
        if re.match(r'^\d+\s+(Subs\.|Ins\.|Omitted|Added|Cls\.|Sch\.)', stripped, re.IGNORECASE) or re.match(r'^\d+\*\s*\*\s*\*$', stripped):
            continue
            
        cleaned_lines.append(line)
        
    cleaned_text = '\n'.join(cleaned_lines).strip()
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text if cleaned_text else raw_text.strip()


def render_citations(sources: list[str]):
    """Render signature citation badges with collapsed statutory text expanders."""
    if not sources:
        return
        
    valid_sources = []
    for src in sources:
        badge_label, doc_title = extract_citation_badge(src)
        if badge_label != "Statute" and "Legal Reference Text" not in doc_title:
            valid_sources.append(src)

    if not valid_sources:
        return

    st.markdown('<div class="citations-header">CITED STATUTORY SOURCES</div>', unsafe_allow_html=True)
    for src in valid_sources:
        badge_label, doc_title = extract_citation_badge(src)
        cleaned_src = clean_statutory_text(src)
        
        # Get first meaningful line for preview snippet
        preview_line = ""
        for line in cleaned_src.split('\n'):
            line_str = line.strip()
            if line_str and not line_str.startswith("ACT:") and not line_str.startswith("SECTION:"):
                preview_line = line_str[:120] + ("..." if len(line_str) > 120 else "")
                break

        preview_html = f'<div class="citation-preview">{html.escape(preview_line)}</div>' if preview_line else ''
        
        st.markdown(
            f"""
            <div class="citation-badge-wrapper">
                <div class="citation-title">
                    <span class="citation-pill-badge">{html.escape(badge_label)}</span>
                    <span>{html.escape(doc_title)}</span>
                </div>
                {preview_html}
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.expander("View Statutory Source Text →"):
            escaped_text = html.escape(cleaned_src)
            st.markdown(f'<div class="statutory-source-box">{escaped_text}</div>', unsafe_allow_html=True)


def run_pipeline_with_loading(question: str):
    """Run RAG pipeline with clean spinner loading state."""
    with st.spinner("Checking the relevant Sections..."):
        # Pass conversation history to pipeline
        answer, retrieved_docs = run_rag_pipeline(question, conversation_history=st.session_state.messages)
    return answer, retrieved_docs


def render_footer():
    st.markdown(
        """
        <div class="app-footer">
            <strong>Law LLM — Pakistani Legal Assistant</strong><br>
            Verified RAG Engine • PPC, CrPC & Constitution<br>
            <span style="opacity: 0.6;">Informational Use Only</span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# STATE INITIALISATION
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_title" not in st.session_state:
    st.session_state.session_title = ""
if "created_at" not in st.session_state:
    st.session_state.created_at = datetime.datetime.now().isoformat()
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ============================================================
# MAIN APP
# ============================================================

render_sidebar()

# PERSISTENT HEADER: Render logo, title, subtitle, and popular topics unconditionally
render_empty_state()

# Handle prefill & chat input
prefill = st.session_state.pop("pending_question", None) if st.session_state.pending_question else None
user_input = st.chat_input(placeholder="Ask about Bail, FIR, Theft... / ضمانت، چوری یا قانون کے بارے میں پوچھیں")

if prefill and not user_input:
    user_input = prefill

# Chat History
if st.session_state.messages:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                render_citations(msg["sources"])

# Active user query processing
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "sources": []})

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="⚖️"):
        try:
            answer, source_chunks = run_pipeline_with_loading(user_input)
        except Exception as e:
            # Log error server-side only
            print(f"[SERVER ERROR] RAG Pipeline Error: {e}", file=sys.stderr)
            err_str = str(e).lower()
            if "413" in err_str or "rate_limit" in err_str or "tokens" in err_str:
                answer = "This query is a bit long — try shortening it or asking about a specific section or topic."
            else:
                answer = "I couldn't find relevant statutory provisions in the PPC, CrPC, or Constitution for that query — try rephrasing, or ask about Bail, FIR, Theft, or Fundamental Rights."
            source_chunks = []

        st.markdown(answer)
        if source_chunks:
            render_citations(source_chunks)
                
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": source_chunks}
    )
    # Save session after each turn
    save_session()

render_footer()
