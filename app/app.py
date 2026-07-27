"""
Law LLM — Pakistani Legal Assistant
Premium AI SaaS UI Redesign
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
    page_title="Law LLM",
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
# HELPER — ICONS (Lucide SVGs)
# ============================================================
SHIELD_SCALES_LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-half"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 22V2"/></svg>'''
BOOK_ICON = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-book-open"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>'''
CHECK_ICON = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-circle-2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>'''
LIGHTBULB_ICON = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-lightbulb"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1.3.5 2.6 1.5 3.5.8.8 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>'''
WARNING_ICON = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-triangle-alert"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'''

# ============================================================
# UI COMPONENTS
# ============================================================

def render_sidebar():
    """Render the redesigned sidebar."""
    with st.sidebar:
        # Branding
        st.markdown(
            f"""
            <div class="sidebar-logo">
                {SHIELD_SCALES_LOGO}
                <div>
                    <h2>LAW LLM</h2>
                    <p>Pakistani Legal Assistant</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr style="margin: 0 0 1rem; border-color: rgba(255,255,255,0.08)">', unsafe_allow_html=True)

        # Sources
        st.markdown(f'<div class="sidebar-section">{BOOK_ICON} Legal Sources</div>', unsafe_allow_html=True)
        sources = ["Pakistan Penal Code", "Constitution", "Criminal Procedure Code"]
        for src in sources:
            st.markdown(
                f"""
                <div class="source-item">
                    <span class="source-icon">{CHECK_ICON}</span> {src}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('<hr style="margin: 1rem 0; border-color: rgba(255,255,255,0.08)">', unsafe_allow_html=True)

        # Examples
        st.markdown(f'<div class="sidebar-section">{LIGHTBULB_ICON} Example Questions</div>', unsafe_allow_html=True)
        suggestions = ["Bail", "FIR", "Theft", "Murder"]
        for s in suggestions:
            if st.button(f"• {s}", key=f"sidebar_{s}"):
                st.session_state.pending_question = s

        # Clear
        st.markdown('<div style="margin-top:1.5rem"></div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

        # Disclaimer
        st.markdown(
            f"""
            <div class="sidebar-disclaimer">
                <strong>{WARNING_ICON} Disclaimer</strong>
                Informational use only.<br>Not legal advice.
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_empty_state():
    """Render the empty state/hero section."""
    st.markdown(
        f"""
        <div class="hero-section">
            <div class="hero-icon">{SHIELD_SCALES_LOGO}</div>
            <div class="hero-title">How can I help today?</div>
            <p class="hero-subtitle">Ask anything about Pakistani law. Get clear explanations backed by exact legal citations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown('<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; margin: 1rem 0 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Popular Questions</div>', unsafe_allow_html=True)
    
    # Suggestions
    pills = ["Bail", "FIR", "Theft", "Murder", "Fundamental Rights"]
    st.markdown('<div class="suggestions-container">', unsafe_allow_html=True)
    cols = st.columns(len(pills))
    for col, pill in zip(cols, pills):
        with col:
            if st.button(pill, key=f"pill_{pill}"):
                st.session_state.pending_question = pill
    st.markdown('</div>', unsafe_allow_html=True)

    # Tech stack
    st.markdown(
        """
        <div class="tech-stack-badges">
            <span>Powered by</span>
            <span>Groq</span>
            <span>Llama 3.3</span>
            <span>ChromaDB</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def parse_reference(raw_chunk_text: str) -> str:
    """Extract a clean title from the raw chunk text (e.g. 'Pakistan Penal Code - Section 302')."""
    lines = raw_chunk_text.strip().split("\\n")
    if len(lines) > 1:
        # Usually the first line contains the act and section info if chunking was done well
        first_line = lines[0].strip()
        if len(first_line) > 10 and len(first_line) < 80:
            return first_line
    return "Legal Document Snippet"

def run_pipeline_with_loading(question: str):
    """Run RAG pipeline with sequential loading messages."""
    status_placeholder = st.empty()
    
    # Sequential loading experience
    steps = [
        "⚖️ Searching legal database...",
        "📚 Retrieving relevant sections...",
        "🧠 Generating legal explanation...",
        "✅ Formatting response..."
    ]
    
    for step in steps:
        with status_placeholder.status(step, expanded=False, state="running"):
            time.sleep(0.5)
            
    with status_placeholder.status(steps[-1], expanded=False, state="running"):
        answer, retrieved_docs = run_rag_pipeline(question)
        
    status_placeholder.empty()
    return answer, retrieved_docs

def render_footer():
    st.markdown(
        """
        <div class="app-footer">
            <strong>Law LLM</strong> — Pakistani Legal Assistant<br>
            Powered by Llama 3.3 • Groq API • ChromaDB • Streamlit<br>
            <span style="opacity: 0.7;">Not Legal Advice</span>
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
            
            # Reference Expanders
            if msg["role"] == "assistant" and msg.get("sources"):
                for src in msg["sources"]:
                    title = parse_reference(src)
                    st.markdown(f'<div class="ref-card-container"><div class="ref-header"><span class="ref-icon">{BOOK_ICON}</span>{title}</div>', unsafe_allow_html=True)
                    with st.expander("View Details →"):
                        st.markdown(f"```text\n{src}\n```")
                    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CHAT INPUT
# ============================================================
prefill = st.session_state.pop("pending_question", None) if st.session_state.pending_question else None

user_input = st.chat_input(placeholder="Ask anything about Pakistani law...")

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
            answer = f"**Error:** Could not connect to the backend. Please check API keys.\n\n`{str(e)}`"
            source_chunks = []

        st.markdown(answer)
        
        if source_chunks:
            for src in source_chunks:
                title = parse_reference(src)
                st.markdown(f'<div class="ref-card-container"><div class="ref-header"><span class="ref-icon">{BOOK_ICON}</span>{title}</div>', unsafe_allow_html=True)
                with st.expander("View Details →"):
                    st.markdown(f"```text\n{src}\n```")
                st.markdown('</div>', unsafe_allow_html=True)
                
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": source_chunks}
    )

render_footer()
