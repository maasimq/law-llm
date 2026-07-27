"""
Law LLM — Pakistani Legal Assistant
Premium Streamlit UI (Redesigned)
====================================
UI-only redesign. All backend logic (RAG pipeline, ChromaDB,
Groq API, embeddings, prompt templates) is unchanged.
Only the presentation layer has been updated.
"""

import sys
import os
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — make backend scripts importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import run_rag_pipeline  # noqa: E402  (backend untouched)

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
# HELPER — UI component builders (pure frontend, no backend)
# ============================================================

def render_sidebar():
    """Render the redesigned sidebar with logo, sources, suggestions, disclaimer."""
    with st.sidebar:
        # --- Logo ---
        st.markdown(
            """
            <div class="sidebar-logo">
                <span style="font-size:2rem">⚖️</span>
                <h2>Law LLM</h2>
                <p>Pakistani Legal Assistant</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- Legal Sources ---
        st.markdown('<div class="sidebar-section">📚 Sources</div>', unsafe_allow_html=True)
        sources = [
            ("#3B82F6", "Pakistan Penal Code"),
            ("#10B981", "Constitution of Pakistan"),
            ("#F59E0B", "Code of Criminal Procedure"),
        ]
        for color, name in sources:
            st.markdown(
                f"""
                <div class="source-item">
                    <span class="source-dot" style="background:{color}"></span>
                    ✓ {name}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --- Suggested Questions (clickable) ---
        st.markdown('<div class="sidebar-section">💡 Try Asking</div>', unsafe_allow_html=True)
        suggestions = ["Bail", "FIR", "Theft", "Fundamental Rights", "Murder"]
        for s in suggestions:
            if st.button(f"• {s}", key=f"sidebar_{s}", use_container_width=True):
                st.session_state.pending_question = s

        # --- Clear chat ---
        st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Conversation", key="clear_chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        # --- Disclaimer ---
        st.markdown(
            """
            <div class="sidebar-disclaimer">
                ⚠️ <strong>Disclaimer</strong><br>
                This assistant provides informational guidance only.
                It is <strong>not legal advice</strong>. Consult a qualified lawyer.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hero():
    """Render the hero section with title, subtitle, feature cards, and stats."""
    st.markdown(
        """
        <div class="hero-section">
            <span class="hero-icon">⚖️</span>
            <div class="hero-title">Law LLM</div>
            <p class="hero-subtitle">
                Pakistan's AI Legal Assistant<br>
                <span style="font-size:0.9rem; color:#64748B;">
                Ask questions about Pakistani law in plain English.<br>
                Powered by Retrieval-Augmented Generation using verified legal sources.
                </span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    st.markdown(
        """
        <div class="cards-row">
            <div class="feature-card">
                <span class="card-icon">⚡</span>
                <div class="card-title">Fast Search</div>
                <div class="card-desc">Instant semantic search through Pakistani law using vector embeddings.</div>
            </div>
            <div class="feature-card">
                <span class="card-icon">📚</span>
                <div class="card-title">Verified Sources</div>
                <div class="card-desc">Only official legal documents — PPC, CrPC, Constitution.</div>
            </div>
            <div class="feature-card">
                <span class="card-icon">🧠</span>
                <div class="card-title">AI Explanation</div>
                <div class="card-desc">Complex legal language explained simply for everyone.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stats row
    st.markdown(
        """
        <div class="stats-row">
            <div class="stat-card">
                <span class="stat-icon">📚</span>
                <span class="stat-value">3 Legal Acts</span>
                <span class="stat-label">Data Sources</span>
            </div>
            <div class="stat-card">
                <span class="stat-icon">📄</span>
                <span class="stat-value">1,000+ Sections</span>
                <span class="stat-label">Legal Passages</span>
            </div>
            <div class="stat-card">
                <span class="stat-icon">⚡</span>
                <span class="stat-value">Fast Responses</span>
                <span class="stat-label">Groq LPU Inference</span>
            </div>
            <div class="stat-card">
                <span class="stat-icon">🔒</span>
                <span class="stat-value">Secure & Private</span>
                <span class="stat-label">Local ChromaDB</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_suggestions():
    """Render clickable suggested-question pills below the hero."""
    st.markdown('<div class="suggestions-label">Suggested Questions</div>', unsafe_allow_html=True)
    pills = [
        "What is Bail?",
        "How to register an FIR?",
        "Punishment for Theft",
        "Fundamental Rights",
        "How does anticipatory bail work?",
        "Constitution Article 25",
    ]
    cols = st.columns(len(pills))
    for col, pill in zip(cols, pills):
        with col:
            if st.button(pill, key=f"pill_{pill}"):
                st.session_state.pending_question = pill


def render_message(role: str, content: str, sources: list = None):
    """Render a single chat message bubble with avatar and optional sources."""
    if role == "user":
        st.markdown(
            f"""
            <div class="msg-user">
                <div class="avatar avatar-user">👤</div>
                <div>
                    <div class="msg-label">You</div>
                    <div class="bubble-user">{content}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="msg-assistant">
                <div class="avatar avatar-assistant">⚖️</div>
                <div style="flex:1; min-width:0;">
                    <div class="msg-label">Law LLM</div>
                    <div class="bubble-assistant">{content}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Reference cards
        if sources:
            st.markdown(
                '<div class="refs-container"><div class="refs-title">📘 Legal References</div>',
                unsafe_allow_html=True,
            )
            for src in sources:
                st.markdown(
                    f'<div class="ref-card">{src}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # Expandable retrieved text
        if sources:
            with st.expander("▼ View Retrieved Legal Text"):
                for i, src in enumerate(sources, 1):
                    st.markdown(
                        f"**Chunk {i}:** `{src}`",
                    )


def run_pipeline_with_steps(question: str):
    """
    Calls the backend RAG pipeline while displaying animated loading steps.
    Returns (answer, source_labels). Backend logic is NOT modified here.
    """
    loading_placeholder = st.empty()

    steps = [
        ("⚖️", "Searching legal database..."),
        ("📚", "Retrieving relevant sections..."),
        ("🧠", "Generating AI explanation..."),
    ]

    # Animate loading steps
    for icon, msg in steps:
        loading_placeholder.markdown(
            f"""
            <div class="loading-step">
                <span class="loading-dot"></span>
                <span>{icon} {msg}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.6)

    # Call the actual backend pipeline (UNCHANGED)
    answer, retrieved_docs = run_rag_pipeline(question)

    # Clear the loading indicator
    loading_placeholder.empty()

    # Build display-friendly source labels from raw retrieved text
    source_labels = [
        f"📄 Chunk {i + 1}: {doc[:120].strip()}..."
        for i, doc in enumerate(retrieved_docs)
    ]

    return answer, source_labels


def render_footer():
    """Render the footer with tech stack badges."""
    st.markdown(
        """
        <div class="app-footer">
            <strong style="color:#CBD5E1">Law LLM</strong> — Pakistani Legal Assistant<br>
            <span style="color:#64748B">Not Legal Advice · For Academic & Research Use Only</span>
            <div class="footer-badges">
                <span class="footer-badge">🤖 Llama 3.3 70B</span>
                <span class="footer-badge">⚡ Groq API</span>
                <span class="footer-badge">🗄️ ChromaDB</span>
                <span class="footer-badge">🎈 Streamlit</span>
                <span class="footer-badge">🏛️ FAST-NUCES Lahore</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SESSION STATE INITIALISATION
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ============================================================
# DISCLAIMER GATE
# ============================================================
if not st.session_state.disclaimer_accepted:
    st.markdown(
        """
        <div style="max-width:560px; margin:8rem auto; text-align:center;">
            <span style="font-size:3rem">⚖️</span>
            <h1 style="font-size:2rem; font-weight:800; margin:0.8rem 0 0.4rem;">Law LLM</h1>
            <p style="color:#CBD5E1; margin-bottom:2rem;">Pakistani Legal Assistant</p>
            <div style="background:#1E293B; border:1px solid rgba(245,158,11,0.3);
                        border-radius:12px; padding:1.2rem 1.5rem; text-align:left;
                        margin-bottom:1.5rem;">
                <p style="color:#F59E0B; font-weight:600; margin:0 0 0.4rem">⚠️ Disclaimer</p>
                <p style="color:#CBD5E1; font-size:0.88rem; line-height:1.65; margin:0;">
                    This tool is for <strong>informational and academic purposes only</strong>.
                    It is not a substitute for professional legal advice. Answers are generated
                    from a curated database and may not reflect the most recent amendments.
                    Always consult a qualified lawyer for legal matters.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("I understand — Enter App", key="accept_disclaimer", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

# ============================================================
# MAIN APP (after disclaimer accepted)
# ============================================================

# Sidebar
render_sidebar()

# Main content area
render_hero()

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# Suggested questions (only when no conversation yet)
if not st.session_state.messages:
    render_suggestions()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# Chat history
if st.session_state.messages:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        render_message(
            role=msg["role"],
            content=msg["content"],
            sources=msg.get("sources"),
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# CHAT INPUT
# ============================================================
# Handle suggestion pills / sidebar button pre-fill
prefill = st.session_state.pop("pending_question", None) if st.session_state.pending_question else None

user_input = st.chat_input(
    placeholder="Ask anything about Pakistani law...",
)

# Allow pill/sidebar button to act as input
if prefill and not user_input:
    user_input = prefill

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input, "sources": []})

    # Render user message bubble immediately on screen
    render_message(role="user", content=user_input)

    # Run pipeline with animated steps
    try:
        answer, source_labels = run_pipeline_with_steps(user_input)
    except Exception as e:
        answer = (
            f"Sorry, an error occurred while processing your question. "
            f"Please check your API key and ChromaDB setup.\n\n**Details:** {str(e)}"
        )
        source_labels = []

    # Append assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": source_labels}
    )

    st.rerun()

# ============================================================
# FOOTER
# ============================================================
render_footer()
