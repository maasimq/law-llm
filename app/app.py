"""
Law LLM — Pakistani Legal Assistant
Institutional Legal Reference Design
====================================
"""

import sys
import os
import logging

# Fix Streamlit watcher bug with PyTorch custom classes
try:
    import torch
    if hasattr(torch, "classes"):
        torch.classes.__path__ = []
except Exception:
    pass

logging.getLogger("chromadb.telemetry.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
os.environ["ANONYMIZED_TELEMETRY"] = "False"
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

from rag_pipeline import run_rag_pipeline, generate_chat_title, detect_language

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
favicon_path = Path(__file__).parent / "favicon.png"
favicon = str(favicon_path) if favicon_path.exists() else "⚖️"

st.set_page_config(
    page_title="Law LLM — Pakistani Legal Assistant",
    page_icon=favicon,
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

# Preconnect to Google Fonts to eliminate FOUT (flash of unstyled text)
st.markdown(
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    unsafe_allow_html=True,
)

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
    elif "constitution" in text_lower or re.search(r'^\s*(\d+[a-zA-Z]?)\b', chunk_text):
        match = re.search(r'article\s*:\s*(\d+[a-z]?)', chunk_text, re.IGNORECASE) or re.search(r'article\s+(\d+[a-z]?)', chunk_text, re.IGNORECASE) or re.search(r'^\s*(\d+[a-zA-Z]?)\b', chunk_text)
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
            st.session_state.chat_mode = data.get("chat_mode", "Layman")
            st.session_state.chat_topic = data.get("chat_topic", "")
            st.session_state.topic_set = bool(st.session_state.chat_topic)
            st.session_state.chat_started = bool(st.session_state.messages) or bool(st.session_state.chat_topic)
            st.session_state.show_topic_input = False
            st.session_state.pop("topic_error", None)
            st.rerun()

def save_session():
    """Save the current chat session to a JSON file."""
    if not st.session_state.messages:
        return
        
    # Do not save sessions that ended in temporary API rate-limit errors
    last_msg = st.session_state.messages[-1]
    if last_msg.get("role") == "assistant" and ("API Limit Reached" in last_msg.get("content", "") or "rate-limited" in last_msg.get("content", "")):
        return

    # Auto-generate 2-3 word title from first user message and topic
    if not st.session_state.session_title or st.session_state.session_title == "New Conversation":
        first_user_msg = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "")
        topic = st.session_state.get("chat_topic", "")
        if first_user_msg or topic:
            try:
                st.session_state.session_title = generate_chat_title(first_user_msg, topic)
            except TypeError:
                combined = f"{topic}: {first_user_msg}" if (topic and first_user_msg) else (topic or first_user_msg)
                st.session_state.session_title = generate_chat_title(combined)
        else:
            st.session_state.session_title = "New Conversation"
        
    history_dir = get_history_dir()
    filepath = history_dir / f"{st.session_state.session_id}.json"
    
    data = {
        "id": st.session_state.session_id,
        "title": st.session_state.session_title,
        "created_at": st.session_state.created_at,
        "messages": st.session_state.messages,
        "chat_mode": st.session_state.chat_mode,
        "chat_topic": st.session_state.get("chat_topic", "")
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def start_new_session():
    """Initialize a brand new chat session."""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.session_title = ""
    st.session_state.created_at = datetime.datetime.now().isoformat()
    st.session_state.chat_topic = ""
    st.session_state.topic_set = False
    st.session_state.chat_started = False
    st.session_state.show_topic_input = False
    st.session_state.pop("topic_error", None)
    st.session_state.pop("_pending_first_input", None)
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

        st.markdown('<hr style="margin: 1.5rem 0 1rem; border-color: rgba(255,255,255,0.06)">', unsafe_allow_html=True)

        # Multi-chat New Button
        if st.button("➕ New Chat", use_container_width=True):
            start_new_session()

        st.markdown('<hr style="margin: 1.5rem 0 1rem; border-color: rgba(255,255,255,0.06)">', unsafe_allow_html=True)

        # Chat History List
        st.markdown('<div class="sidebar-section">Recent Chats</div>', unsafe_allow_html=True)
        sessions = load_all_sessions()
        
        if not sessions:
            empty_state_html = """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem 0; opacity: 0.5;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 8px;">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                </svg>
                <span style="font-size: 0.85rem; font-weight: 500;">No chat history</span>
            </div>
            """
            st.markdown(empty_state_html, unsafe_allow_html=True)
        else:
            for s in sessions:
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    is_active = (s["id"] == st.session_state.get("session_id"))
                    btn_type = "primary" if is_active else "secondary"
                    display_title = s['title']
                    if len(display_title) > 34:
                        display_title = display_title[:32] + "..."
                    
                    if st.button(display_title, key=f"load_{s['id']}", use_container_width=True, type=btn_type):
                        load_session(s["id"])
                with col2:
                    if st.button(":material/delete:", key=f"del_{s['id']}", help="Delete chat"):
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


def sync_chat_mode_from_pill(widget_key: str):
    val = st.session_state.get(widget_key)
    if not val:
        current = st.session_state.get("chat_mode", "Layman")
        fallback_val = "🗣️ Layman" if current == "Layman" else "⚖️ Advocate"
        st.session_state[widget_key] = fallback_val
        st.session_state.chat_mode = "Layman" if "Layman" in fallback_val else "Advocate"
    else:
        st.session_state.chat_mode = "Layman" if "Layman" in val else "Advocate"

def render_compact_header():
    """Render the compact mode badge shown during active chat."""
    current_mode = st.session_state.get("chat_mode", "Layman")
    current_topic = st.session_state.get("chat_topic", "")
    mode_icon = "🗣️" if current_mode == "Layman" else "⚖️"
    mode_label = f"{mode_icon} {current_mode} Mode"
    topic_html = ""
    if current_topic:
        topic_html = (
            f' &nbsp;·&nbsp; <span style="background:rgba(212,175,55,0.10); color:#D4AF37; '
            f'padding:4px 14px; border-radius:16px; font-size:0.82rem; font-weight:500; '
            f'border:1px solid rgba(212,175,55,0.30);">📌 {html.escape(current_topic)}</span>'
        )
    st.markdown(
        f'<div style="display:flex; justify-content:center; align-items:center; gap:10px; '
        f'margin-top:0.2rem; margin-bottom:0.8rem; flex-wrap:wrap;">'
        f'<span style="background:rgba(212,175,55,0.13); color:#D4AF37; padding:5px 18px; '
        f'border-radius:20px; font-size:0.88rem; font-weight:600; '
        f'border:1px solid rgba(212,175,55,0.4);">{mode_label}</span>'
        f'{topic_html}</div>',
        unsafe_allow_html=True
    )


def render_hero_landing():
    """Render the full hero landing page with title, mode toggle, and topic section."""
    current_mode = st.session_state.get("chat_mode", "Layman")

    # A. Hero Title
    st.markdown(
        f"""
        <div class="hero-section" style="padding-bottom: 0.8rem;">
            <div class="hero-section-mark-container">{SECTION_MARK_SVG}</div>
            <div class="hero-title">Pakistani Legal Assistant</div>
            <p class="hero-subtitle">Search statutory law and constitutional provisions.</p>
            <p class="hero-subtitle urdu-subtitle" style="margin-top: 0.3rem; margin-bottom: 0.6rem; opacity: 0.8; font-family: 'Noto Nastaliq Urdu', serif;">(آپ قانون کے متعلق سوالات اردو میں بھی پوچھ سکتے ہیں)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # B. Mode Segmented Toggle
    default_pill = "🗣️ Layman" if current_mode == "Layman" else "⚖️ Advocate"
    st.session_state.hero_mode_pill = default_pill
    st.markdown('<div style="display: flex; justify-content: center; margin-top: 0.2rem; margin-bottom: 0.2rem;">', unsafe_allow_html=True)
    selected_mode = st.pills(
        "HeroModeToggle",
        options=["🗣️ Layman", "⚖️ Advocate"],
        selection_mode="single",
        label_visibility="collapsed",
        key="hero_mode_pill",
        on_change=lambda: sync_chat_mode_from_pill("hero_mode_pill")
    )
    st.markdown('</div>', unsafe_allow_html=True)
    if selected_mode:
        st.session_state.chat_mode = "Layman" if "Layman" in selected_mode else "Advocate"

    st.markdown(
        '<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 0.2rem; margin-bottom: 1.5rem;">'
        'Advocate mode enables FIR & document drafting.'
        '</div>',
        unsafe_allow_html=True
    )

    # C. Chat Topic section
    if not st.session_state.get("topic_set"):
        _, col, _ = st.columns([1, 2.2, 1])
        with col:
            st.markdown(
                """
                <div class="topic-section-header">
                    <h3 class="topic-heading">What's this chat about?</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            if not st.session_state.get("show_topic_input"):
                st.markdown(
                    '<p class="topic-hint">Focus conversation on a topic (optional)</p>',
                    unsafe_allow_html=True
                )
                st.markdown('<div class="topic-btn-container">', unsafe_allow_html=True)
                tc1, tc2 = st.columns([1, 1])
                with tc1:
                    if st.button("Set Topic", use_container_width=True, type="primary"):
                        st.session_state.show_topic_input = True
                        st.session_state.pop("topic_error", None)
                        st.rerun()
                with tc2:
                    if st.button("Skip", use_container_width=True, type="secondary"):
                        st.session_state.chat_topic = ""
                        st.session_state.topic_set = True
                        st.session_state.show_topic_input = False
                        st.session_state.pop("topic_error", None)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                def handle_topic_submit():
                    val = st.session_state.get("topic_input_field", "").strip()
                    if val:
                        st.session_state.pop("topic_error", None)
                        st.session_state.chat_topic = val
                        st.session_state.topic_set = True
                        st.session_state.show_topic_input = False
                        save_session()
                    else:
                        st.session_state.topic_error = "Please enter a topic (at least 1 word)."

                st.markdown(
                    '<p class="topic-hint">Enter topic (at least 1 word):</p>',
                    unsafe_allow_html=True
                )
                topic_input = st.text_input(
                    "Chat topic",
                    placeholder="e.g. Bail, FIR procedure, Theft under PPC...",
                    label_visibility="collapsed",
                    key="topic_input_field",
                    on_change=handle_topic_submit
                )

                if st.session_state.get("topic_error"):
                    st.markdown(
                        f'<p class="topic-error-msg">{html.escape(st.session_state.topic_error)}</p>',
                        unsafe_allow_html=True
                    )

                st.markdown('<div class="topic-btn-container">', unsafe_allow_html=True)
                tc1, tc2 = st.columns([1, 1])
                with tc1:
                    if st.button("Confirm Topic", use_container_width=True, type="primary"):
                        handle_topic_submit()
                        st.rerun()
                with tc2:
                    if st.button("Cancel", use_container_width=True, type="secondary"):
                        st.session_state.show_topic_input = False
                        st.session_state.pop("topic_error", None)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


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
    # Prevent markdown from turning section numbers like "155. " into giant ordered list items (<ol><li>)
    cleaned_text = re.sub(r'^\s*(\d+[A-Za-z]?)\.\s+', r'\1 — ', cleaned_text, flags=re.MULTILINE)
    # Clean OCR schedule table artifacts (e.g. Ditto .. Ditto, 5[May 5[Summons])
    cleaned_text = re.sub(r'\bDitto\s*\.\.\s*', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'\bDitto\b', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'\d+\[([^\]]+)\]', r'\1', cleaned_text)
    cleaned_text = re.sub(r'\[|\}', '', cleaned_text)
    cleaned_text = re.sub(r'[ \t]{2,}', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text if cleaned_text else raw_text.strip()


def render_markdown_rtl(text: str):
    """Renders text in RTL format only if it is predominantly Urdu/Arabic text."""
    if not text:
        return

    # Normalize standalone bold subheadings so they consistently have a trailing colon
    text = re.sub(r'^(\s*\*\*[A-Za-z0-9\s/&—\-\(\)]+?)\*\*(\s*)$', r'\1:**\2', text, flags=re.MULTILINE)

    urdu_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    is_predominantly_urdu = (urdu_chars > 20 and urdu_chars > latin_chars) or (urdu_chars > 0 and latin_chars == 0)

    if is_predominantly_urdu:
        # We wrap in a div but also use st.markdown. 
        # Streamlit parses markdown inside div if separated by newlines.
        st.markdown(
            f'<div dir="rtl" style="text-align: right; font-family: \'Jameel Noori Nastaleeq\', \'Noto Nastaliq Urdu\', sans-serif; font-size: 1.15rem; line-height: 2;">\n\n{text}\n\n</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(text)


def filter_cited_chunks(answer: str, source_chunks: list[str]) -> list[str]:
    """Return chunks whose (Act, Section) pair appears in the LLM's answer or cited sources block."""
    if not source_chunks or not answer:
        return []

    # If the answer is an explicit refusal, return empty list
    ans_lower = answer.lower()
    if ("restricted to advocate mode" in ans_lower or 
        "outside the scope" in ans_lower or 
        "not currently in my legal database" in ans_lower or
        "i am a legal assistant for pakistani law" in ans_lower):
        return []

    markers = (
        "### Cited Statutory Sources",
        "### Statutory Sources",
        "### متعلقہ سیکشنز",
        "### متعلقہ دفعات",
        "### قانونی دفعات",
        "### قانونی مآخذ",
        "### حوالہ جات",
        "### قوانین و دفعات",
    )
    
    cited_block = ""
    for marker in markers:
        if marker in answer:
            cited_block = answer.split(marker, 1)[1]
            break
            
    # Search target text: the cited block if present, otherwise the entire answer
    search_target = cited_block if cited_block else answer
    search_target_lower = search_target.lower()

    years = {"1860", "1898", "1973", "1979", "1984", "2016", "2018", "2021", "2022", "2023", "2024", "2025", "2026"}
    
    # Extract all section/article numbers mentioned in answer/block
    mentioned_nums = set(re.findall(r'\b\d+[a-zA-Z]?\b', search_target)) - years
    
    # Also detect Urdu numeral words if present
    urdu_sec_map = {"302": "302", "379": "379", "392": "392", "489": "489", "497": "497", "498": "498", "154": "154", "22": "22", "561": "561", "10": "10", "10A": "10A", "14": "14", "19": "19", "25": "25", "199": "199", "295": "295", "156": "156"}
    for k in urdu_sec_map:
        if k in search_target:
            mentioned_nums.add(k)

    filtered = []
    for chunk in source_chunks:
        act_match = re.search(r'ACT:\s*(.+)', chunk, re.IGNORECASE)
        sec_match = re.search(r'(?:SECTION(?:/ARTICLE)?|ARTICLE):\s*(\d+[a-zA-Z]?)', chunk, re.IGNORECASE)
        
        sec_num = None
        if sec_match:
            sec_num = sec_match.group(1).upper()
        else:
            first_match = re.search(r'^\s*(\d+[a-zA-Z]?)\b', chunk)
            if first_match:
                sec_num = first_match.group(1).upper()

        # If section is explicitly extracted from chunk and found in answer text
        if sec_num:
            # Check direct number match (e.g. "302", "489F", "10A")
            sec_base = re.sub(r'[^0-9]', '', sec_num)
            if (sec_num in mentioned_nums or 
                sec_base in mentioned_nums or 
                sec_num.lower() in search_target_lower or 
                (sec_base and sec_base in search_target_lower)):
                if chunk not in filtered:
                    filtered.append(chunk)
            elif not mentioned_nums:
                # If no numbers parsed, keep top retrieved chunks
                if chunk not in filtered:
                    filtered.append(chunk)
        else:
            if chunk not in filtered:
                filtered.append(chunk)
            
    # If filtered is still empty but source_chunks exist and answer is substantive, retain up to 3 chunks
    if not filtered and source_chunks:
        filtered = source_chunks[:3]

    return filtered[:3]


def extract_verdict_badge(answer: str) -> str:
    """Never display top verdict summary banners in responses (user request)."""
    return ""


def render_citations(sources: list[str]):
    """Render signature citation badges with collapsed statutory text expanders and legal currency signals."""
    if not sources:
        return
        
    valid_sources = []
    for src in sources:
        badge_label, doc_title = extract_citation_badge(src)
        if badge_label != "Statute" and "Legal Reference Text" not in doc_title:
            valid_sources.append(src)

    if not valid_sources:
        return

    st.markdown(
        '<div class="statutory-module-container">'
        '<div class="citations-header">'
        '<span class="module-icon">📖</span>'
        '<span>CITED STATUTORY SOURCES (قوانین و دفعات)</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    for src in valid_sources:
        badge_label, doc_title = extract_citation_badge(src)
        cleaned_src = clean_statutory_text(src)
        
        # Get first meaningful line for preview snippet
        preview_line = ""
        for line in cleaned_src.split('\n'):
            line_str = line.strip()
            if line_str and not line_str.startswith("ACT:") and not line_str.startswith("SECTION:"):
                preview_line = line_str[:130] + ("..." if len(line_str) > 130 else "")
                break

        preview_html = f'<div class="citation-preview">{html.escape(preview_line)}</div>' if preview_line else ''
        
        badge_card_html = (
            f'<div class="citation-badge-wrapper">'
            f'<div class="citation-title">'
            f'<span class="citation-pill-badge">{html.escape(badge_label)}</span>'
            f'<span class="citation-doc-name">{html.escape(doc_title)}</span>'
            f'</div>'
            f'{preview_html}'
            f'</div>'
        )
        st.markdown(badge_card_html, unsafe_allow_html=True)
        
        with st.expander(f"▾ View Statutory Source Excerpt — {html.escape(doc_title)} →"):
            escaped_text = html.escape(cleaned_src)
            formatted_html_text = escaped_text.replace('\n\n', '<br><br>').replace('\n', '<br>')
            statutory_box_html = (
                f'<div class="statutory-source-box">'
                f'<div class="statutory-code-content">{formatted_html_text}</div>'
                f'<div class="statutory-meta-footer">'
                f'<span class="statutory-verified-tag">🛡️ Verified Authentic Text</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(statutory_box_html, unsafe_allow_html=True)


def render_case_precedents(cases: list[dict], show_urdu: bool = False):
    """Render signature judicial precedent cards with status badges, ratio decidendi, and customized expanders.
    Shows Urdu ratio summary only when query/response is in Urdu or Roman Urdu.
    """
    if not cases:
        return

    st.markdown(
        '<div class="precedent-module-container">'
        '<div class="precedent-header">'
        '<span class="module-icon">⚖️</span>'
        '<span>RELEVANT JUDICIAL PRECEDENTS (عدالتی نظائر)</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    for c in cases:
        citation = c.get("citation", "Case Law")
        title = c.get("case_title", "Supreme Court / High Court Ruling")
        court = c.get("court", "Court of Pakistan")
        year = c.get("year", "")
        ratio = c.get("ratio_decidendi", "")
        urdu_ratio = c.get("urdu_ratio", "")
        facts = c.get("facts_summary", "")
        ruling = c.get("disposition", "")
        statutes = c.get("statutes_cited", "")
        status_val = c.get("status", "Good Law")

        # Status pill: only display if explicitly overruled or distinguished
        if status_val.lower() == "overruled":
            status_html = '<span class="precedent-status-badge status-overruled">✗ Overruled</span>'
        elif status_val.lower() == "distinguished":
            status_html = '<span class="precedent-status-badge status-distinguished">⚠ Distinguished</span>'
        else:
            status_html = ''

        precedent_card_html = (
            f'<div class="precedent-badge-wrapper">'
            f'<div class="precedent-title">'
            f'<span class="precedent-pill-badge">📜 {html.escape(citation)}</span>'
            f'<span class="precedent-case-name">{html.escape(title)}</span>'
            f'{status_html}'
            f'</div>'
            f'<div class="precedent-ratio">'
            f'<strong class="precedent-label">Legal Principle (Ratio Decidendi):</strong> {html.escape(ratio)}'
            f'</div>'
            f'</div>'
        )
        st.markdown(precedent_card_html, unsafe_allow_html=True)
        
        toggle_label = f"▾ View Full Judgment — {title}, {citation} →"
        with st.expander(toggle_label):
            statutes_html = f"<div class='case-detail-row'><strong class='detail-label'>Statutes Applied:</strong> <span class='detail-val'>{html.escape(statutes)}</span></div>" if statutes else ""
            ruling_html = f"<div class='case-detail-row'><strong class='detail-label'>Court Ruling / Disposition:</strong> <span class='detail-val-highlight'>{html.escape(ruling)}</span></div>" if ruling else ""
            facts_html = f"<div class='case-detail-row' style='margin-top: 0.5rem;'><strong class='detail-label'>Facts of the Case:</strong> <span class='detail-val-facts'>{html.escape(facts)}</span></div>" if facts else ""
            
            urdu_html = ""
            if show_urdu and urdu_ratio:
                urdu_html = (
                    f'<div class="urdu-summary-box" dir="rtl" lang="ur">'
                    f'<div class="urdu-header-label">خلاصہ و قانونی نظیر (Urdu Summary):</div>'
                    f'<div class="urdu-text-content">{html.escape(urdu_ratio)}</div>'
                    f'</div>'
                )
            
            details_box_html = (
                f'<div class="statutory-source-box case-details-box">'
                f'<div class="case-detail-row"><strong class="detail-label">Forum & Benchmark:</strong> <span class="detail-val">{html.escape(court)} ({year})</span></div>'
                f'{statutes_html}'
                f'{ruling_html}'
                f'{facts_html}'
                f'{urdu_html}'
                f'<div class="case-meta-footer">'
                f'<span class="case-verified-tag">🛡️ Reported Judgment Precedent</span>'
                f'<span class="case-citation-tag">🏛️ Citation: {html.escape(citation)}</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(details_box_html, unsafe_allow_html=True)


def _loading(placeholder, msg: str):
    placeholder.markdown(f'<div class="rag-loading">{msg}</div>', unsafe_allow_html=True)


def run_pipeline_with_loading(question: str, placeholder=None):
    """Run RAG pipeline with sequential stage-based loading messages."""
    from rag_pipeline import answer_question

    if placeholder is None:
        placeholder = st.empty()
    mode_val = st.session_state.get("chat_mode", "Layman").lower()
    chat_topic = st.session_state.get("chat_topic", "") or None

    _loading(placeholder, "Translating query & analyzing laws...")
    res = answer_question(
        question,
        conversation_history=st.session_state.messages,
        mode=mode_val,
        on_stage=lambda msg: _loading(placeholder, msg),
        chat_topic=chat_topic,
    )
    placeholder.empty()
    
    if len(res) == 4:
        answer, retrieved_docs, urdu_verified, case_precedents = res
    else:
        answer, retrieved_docs, urdu_verified = res[0], res[1], res[2]
        case_precedents = []
        
    return answer, retrieved_docs, urdu_verified, case_precedents


# Footer removed as per user request


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
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "Layman"
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "chat_topic" not in st.session_state:
    st.session_state.chat_topic = ""
if "topic_set" not in st.session_state:
    st.session_state.topic_set = False
if "show_topic_input" not in st.session_state:
    st.session_state.show_topic_input = False

# ============================================================
# MAIN APP
# ============================================================

render_sidebar()

# 1. CAPTURE USER INPUT FIRST
#    st.chat_input is a FIXED-POSITION widget — it always renders at the
#    bottom of the page regardless of where it's called in code.
#    We call it first so we can use its return value to set state BEFORE
#    rendering the header/hero.
mode_placeholder = "Ask about Bail, FIR, Theft... / ضمانت، چوری یا قانون کے بارے میں پوچھیں"
if st.session_state.get("chat_mode") == "Advocate":
    mode_placeholder = "Draft an FIR, prepare a case brief, or ask a legal question..."

user_input = st.chat_input(placeholder=mode_placeholder, key="main_chat_input")

# Handle prefill from sidebar
prefill = st.session_state.pop("pending_question", None) if st.session_state.get("pending_question") else None
if prefill and not user_input:
    user_input = prefill

# Recover from interrupted generation (e.g. user clicked sidebar during generation)
if not user_input and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages.pop()["content"]

# 2. LOCK STATE: the moment we have user input, messages, OR a topic set,
#    hero must be hidden and mode pill must be locked
has_chat_started = bool(user_input or st.session_state.messages or
                        st.session_state.get("chat_started") or
                        st.session_state.get("topic_set") or
                        st.session_state.get("pending_question"))
if has_chat_started:
    st.session_state.chat_started = True
    st.session_state.topic_set = True

# 3. RENDER HEADER + HERO
#    The hero section lives inside st.empty() so it gets INSTANTLY cleared
#    when chat starts — no leftover DOM from the previous frame.
if has_chat_started:
    render_compact_header()

hero_placeholder = st.empty()
if not has_chat_started:
    with hero_placeholder.container():
        render_hero_landing()
# When has_chat_started is True, hero_placeholder stays empty → previous hero is wiped

# Chat History
if st.session_state.messages:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        msg_mode = msg.get("mode", st.session_state.chat_mode.lower())
        asst_icon = "⚖️" if msg_mode == "advocate" else "🗣️"
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else asst_icon):
            if msg["role"] == "assistant":
                is_msg_refusal = (
                    "restricted to Advocate mode" in msg["content"] or
                    "legal assistant for Pakistani law" in msg["content"] or
                    "legal advocate for Pakistani law" in msg["content"] or
                    "outside the scope" in msg["content"] or
                    "not currently in my legal database" in msg["content"]
                )
                if not is_msg_refusal:
                    verdict_html = extract_verdict_badge(msg["content"])
                    if verdict_html:
                        st.markdown(verdict_html, unsafe_allow_html=True)

            render_markdown_rtl(msg["content"])

            if msg["role"] == "assistant":
                if msg.get("sources"):
                    render_citations(msg["sources"])
                if msg.get("cases"):
                    msg_content = msg.get("content", "")
                    msg_is_urdu = (detect_language(msg_content) == "urdu")
                    render_case_precedents(msg["cases"], show_urdu=msg_is_urdu)

# Active user query processing
if user_input:
    current_active_mode = st.session_state.get("chat_mode", "Layman")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "sources": [],
        "cases": [],
        "mode": current_active_mode.lower()
    })

    with st.chat_message("user", avatar="👤"):
        render_markdown_rtl(user_input)

    # Sleek floating loading pill OUTSIDE assistant message box (no giant empty container box)
    status_placeholder = st.empty()
    try:
        from rag_pipeline import filter_cited_cases
        answer, raw_source_chunks, urdu_verified, raw_cases = run_pipeline_with_loading(user_input, placeholder=status_placeholder)
        source_chunks = filter_cited_chunks(answer, raw_source_chunks)
        cited_cases = filter_cited_cases(answer, raw_cases)
    except Exception as e:
        print(f"[SERVER ERROR] RAG Pipeline Error: {e}", file=sys.stderr)
        err_str = str(e).lower()
        if "429" in err_str or "rate_limit" in err_str or "tokens" in err_str:
            answer = "⚠️ **API Limit Reached / Server Busy**\n\nThe LLM service is temporarily rate-limited. Please wait a few seconds and try again."
        elif "413" in err_str:
            answer = "⚠️ **Query Too Long**\n\nThis query is too long — please try shortening it or asking about a specific section or topic."
        else:
            answer = f"⚠️ **System Notice**\n\nCould not complete generation: `{html.escape(str(e))}`\n\nPlease retry or choose a topic from the sidebar."
        source_chunks = []
        raw_source_chunks = []
        cited_cases = []
        urdu_verified = True
    finally:
        status_placeholder.empty()

    is_refusal = (
        "restricted to Advocate mode" in answer or
        "legal assistant for Pakistani law" in answer or
        "legal advocate for Pakistani law" in answer or
        "outside the scope" in answer or
        "not currently in my legal database" in answer
    )

    asst_icon = "⚖️" if current_active_mode == "Advocate" else "🗣️"
    with st.chat_message("assistant", avatar=asst_icon):
        if not is_refusal:
            verdict_html = extract_verdict_badge(answer)
            if verdict_html:
                st.markdown(verdict_html, unsafe_allow_html=True)

        render_markdown_rtl(answer)

        if not urdu_verified:
            st.markdown(
                '<div style="margin-top:0.8rem; padding:10px 14px; background:rgba(255,165,0,0.08); '
                'border:1px solid rgba(255,165,0,0.30); border-left:3px solid #FFA500; '
                'border-radius:6px; font-size:0.85rem; line-height:1.6;">'
                '<span style="color:#FFA500; font-weight:600;">⚠️ Verification Notice</span><br>'
                '<span style="color:#FFA500;">اردو جواب کی تصدیق نہیں ہو سکی — براہ کرم کسی مستند ذریعے سے تصدیق کریں۔</span><br>'
                '<span style="color:rgba(255,165,0,0.7); font-size:0.78rem;">'
                'This Urdu response could not be fully verified. Please cross-check with an authoritative source.</span>'
                '</div>',
                unsafe_allow_html=True
            )

        if is_refusal:
            source_chunks = []
            cited_cases = []

        if source_chunks and not is_refusal:
            render_citations(source_chunks)
            
        if cited_cases and not is_refusal:
            query_is_urdu = (detect_language(user_input) == "urdu")
            render_case_precedents(cited_cases, show_urdu=query_is_urdu)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": source_chunks if not is_refusal else [],
            "cases": cited_cases if not is_refusal else [],
            "mode": current_active_mode.lower()
        }
    )
    save_session()
    st.rerun()
