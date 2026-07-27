"""
Law LLM — Pakistani Legal Assistant
Institutional Legal Reference Design
====================================
"""

import sys
import os
import time
from pathlib import Path
import re

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
    Extract a concise citation badge (e.g. 'PPC § 302', 'Art. 25', 'CrPC § 154')
    and document title from raw chunk text.
    """
    text_lower = chunk_text.lower()
    
    # Constitution
    if "constitution" in text_lower or "article" in text_lower:
        match = re.search(r'article\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE)
        badge = f"Art. {match.group(1).upper()}" if match else "Constitution"
        return badge, "Constitution of Pakistan"
    
    # Pakistan Penal Code
    elif "penal code" in text_lower or "ppc" in text_lower:
        match = re.search(r'section\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE)
        badge = f"PPC § {match.group(1).upper()}" if match else "PPC"
        return badge, "Pakistan Penal Code, 1860"
    
    # Code of Criminal Procedure
    elif "criminal procedure" in text_lower or "crpc" in text_lower:
        match = re.search(r'section\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE)
        badge = f"CrPC § {match.group(1).upper()}" if match else "CrPC"
        return badge, "Code of Criminal Procedure, 1898"
    
    # Fallback section regex
    sec_match = re.search(r'section\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE)
    if sec_match:
        return f"§ {sec_match.group(1).upper()}", "Statutory Authority"
        
    return "Ref. §", "Legal Reference Text"


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

        # Clear
        if st.button("Clear Conversation", key="clear_chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

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
            <p class="hero-subtitle">Search statutory law and constitutional provisions with exact section citations.</p>
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


def render_citations(sources: list[str]):
    """Render signature citation badges in accent color with expanders for full text."""
    if not sources:
        return
        
    st.markdown('<div class="citations-header">CITED STATUTORY SOURCES</div>', unsafe_allow_html=True)
    for src in sources:
        badge_label, doc_title = extract_citation_badge(src)
        st.markdown(
            f"""
            <div class="citation-badge-wrapper">
                <div class="citation-title">
                    <span class="citation-pill-badge">{badge_label}</span>
                    <span>{doc_title}</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        with st.expander("View Statutory Source Text →"):
            st.markdown(f"```text\n{src}\n```")
        st.markdown('</div>', unsafe_allow_html=True)


def run_pipeline_with_loading(question: str):
    """Run RAG pipeline with clean spinner loading state."""
    with st.spinner("Checking the relevant Sections..."):
        answer, retrieved_docs = run_rag_pipeline(question)
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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ============================================================
# MAIN APP
# ============================================================

render_sidebar()

if not st.session_state.messages:
    render_empty_state()

# Chat History
if st.session_state.messages:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                render_citations(msg["sources"])

# ============================================================
# CHAT INPUT
# ============================================================
prefill = st.session_state.pop("pending_question", None) if st.session_state.pending_question else None

user_input = st.chat_input(placeholder="Ask about Bail, FIR, Theft, or Constitutional Rights...")

if prefill and not user_input:
    user_input = prefill

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

render_footer()
