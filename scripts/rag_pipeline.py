import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer, CrossEncoder

from bm25_index import BM25KeywordIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = "llama-3.3-70b-versatile"
REFUSAL_SENTENCE = "I do not have sufficient information in the provided legal text to answer this question."

# ============================================================
# LEGAL ALIASES — map common terms/shorthand to exact (Act, Section) references
# ============================================================
LEGAL_ALIASES = {
    "fir": [("Code of Criminal Procedure, 1898", "154")],
    "first information report": [("Code of Criminal Procedure, 1898", "154")],
    "bail": [("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "498")],
    "theft": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "steal": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "steals": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "stolen": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "stole": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "murder": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "robbery": [("Pakistan Penal Code, 1860", "390"), ("Pakistan Penal Code, 1860", "392")],
    "dacoity": [("Pakistan Penal Code, 1860", "391"), ("Pakistan Penal Code, 1860", "395")],
    "kidnapping": [("Pakistan Penal Code, 1860", "359"), ("Pakistan Penal Code, 1860", "360")],
    "abduction": [("Pakistan Penal Code, 1860", "362")],
    "forgery": [("Pakistan Penal Code, 1860", "463"), ("Pakistan Penal Code, 1860", "464")],
    "defamation": [("Pakistan Penal Code, 1860", "499"), ("Pakistan Penal Code, 1860", "500")],
    "adultery": [("Pakistan Penal Code, 1860", "497")],
    "fair trial": [("Constitution of Pakistan", "10A")],
    "right to fair trial": [("Constitution of Pakistan", "10A")],
    "fundamental rights": [("Constitution of Pakistan", "8")],
    "arrest": [("Constitution of Pakistan", "10"), ("Code of Criminal Procedure, 1898", "54")],
    "detention": [("Constitution of Pakistan", "10")],
    "search warrant": [("Code of Criminal Procedure, 1898", "96"), ("Code of Criminal Procedure, 1898", "97")],
    "freedom of speech": [("Constitution of Pakistan", "19")],
    "right to education": [("Constitution of Pakistan", "25A")],
    "equality": [("Constitution of Pakistan", "25")],
    "slavery": [("Constitution of Pakistan", "11")],
    "forced labour": [("Constitution of Pakistan", "11")],
    "privacy": [("Constitution of Pakistan", "14")],
    "dignity": [("Constitution of Pakistan", "14")],
    "property": [("Constitution of Pakistan", "23"), ("Constitution of Pakistan", "24")],
    "religion": [("Constitution of Pakistan", "20")],
    "mischief": [("Pakistan Penal Code, 1860", "425"), ("Pakistan Penal Code, 1860", "426")],
    "cheating": [("Pakistan Penal Code, 1860", "415"), ("Pakistan Penal Code, 1860", "420")],
    "hurt": [("Pakistan Penal Code, 1860", "332"), ("Pakistan Penal Code, 1860", "337")],
    "rash driving": [("Pakistan Penal Code, 1860", "279"), ("Pakistan Penal Code, 1860", "320"), ("Pakistan Penal Code, 1860", "337G")],
    "negligent driving": [("Pakistan Penal Code, 1860", "279"), ("Pakistan Penal Code, 1860", "320"), ("Pakistan Penal Code, 1860", "337G")],
    "criminal conspiracy": [("Pakistan Penal Code, 1860", "120A"), ("Pakistan Penal Code, 1860", "120B")],
    "conspiracy": [("Pakistan Penal Code, 1860", "120A"), ("Pakistan Penal Code, 1860", "120B")],
    # --- Urdu Aliases (Bilingual Support) ---
    "ایف آئی آر": [("Code of Criminal Procedure, 1898", "154")],
    "ضمانت": [("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "498")],
    "چوری": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379")],
    "قتل": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "ڈکیتی": [("Pakistan Penal Code, 1860", "391"), ("Pakistan Penal Code, 1860", "395")],
    "لوٹ مار": [("Pakistan Penal Code, 1860", "390"), ("Pakistan Penal Code, 1860", "392")],
    "اغوا": [("Pakistan Penal Code, 1860", "359"), ("Pakistan Penal Code, 1860", "360")],
    "جعلسازی": [("Pakistan Penal Code, 1860", "463"), ("Pakistan Penal Code, 1860", "464")],
    "بنیادی حقوق": [("Constitution of Pakistan", "8")],
    "منصفانہ مقدمہ": [("Constitution of Pakistan", "10A")],
    "گرفتاری": [("Constitution of Pakistan", "10"), ("Code of Criminal Procedure, 1898", "54")],
    "آزادی اظہار": [("Constitution of Pakistan", "19")],
    "تعلیم کا حق": [("Constitution of Pakistan", "25A")],
    "مساوات": [("Constitution of Pakistan", "25")],
    "دھوکہ": [("Pakistan Penal Code, 1860", "415"), ("Pakistan Penal Code, 1860", "420")],
}


CONVERSATIONAL_PATTERNS = re.compile(
    r'^\s*(hi+|hello+|hey+|thanks?|thank you|ok|okay|bye|good\s*(morning|evening|afternoon|night)?|'  
    r'who are you|what are you|how are you|what can you do|help me|test|testing|'  
    r'سلام|ہیلو|شکریہ|ٹھیک ہے|آپ کون ہیں)\s*[!?.]*\s*$',
    re.IGNORECASE
)


def is_conversational(query: str) -> bool:
    """Return True if the query is purely conversational with no legal substance."""
    stripped = query.strip()
    if len(stripped.split()) <= 3 and CONVERSATIONAL_PATTERNS.match(stripped):
        return True
    return False


def detect_language(text: str) -> str:
    """Detect if the query is in Urdu (Unicode range 0600-06FF) or English."""
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return "urdu" if urdu_chars > len(text) * 0.3 else "english"


def load_prompt_template() -> str:
    """Load the Layman prompt template used for the legal-answer generation step."""
    template_path = PROJECT_ROOT / "scripts" / "prompt_template.txt"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as handle:
            return handle.read()
    return ""

def load_advocate_prompt_template() -> str:
    """Load the Advocate prompt template for drafting FIRs and case briefs."""
    template_path = PROJECT_ROOT / "scripts" / "advocate_prompt_template.txt"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as handle:
            return handle.read()
    return ""

def retrieve_context(query_text: str, collection, embed_model, top_k: int = 3, filter_act: str | None = None, max_distance: float = 0.50):
    """Retrieve the top matching dense vector chunks from ChromaDB, filtered by similarity distance."""
    prefixed_query = "Represent this sentence for searching relevant passages: " + query_text
    query_embedding = embed_model.encode(prefixed_query, normalize_embeddings=True).tolist()
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"]
    }
    if filter_act:
        query_params["where"] = {"act_name": filter_act}

    results = collection.query(**query_params)
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    filtered_docs = []
    filtered_metas = []
    filtered_dists = []
    for doc, dist, meta in zip(docs, distances, metadatas):
        # Cosine distance: lower is more similar (0 = identical, 1 = orthogonal)
        if dist <= max_distance:
            filtered_docs.append(doc)
            filtered_metas.append(meta)
            filtered_dists.append(dist)

    return filtered_docs, filtered_metas, filtered_dists


def retrieve_bm25_context(query_text: str, filter_act: str | None = None, top_k: int = 2):
    """Retrieve additional keyword-based chunks using the BM25 index with Act filtering.
    Returns list of text strings (backward-compatible)."""
    scored = retrieve_bm25_scored(query_text, filter_act=filter_act, top_k=top_k)
    return [item["text"] for item in scored]


def retrieve_bm25_scored(query_text: str, filter_act: str | None = None, top_k: int = 2):
    """Retrieve keyword-based chunks with BM25 scores and metadata for hybrid fusion."""
    try:
        bm25_index = BM25KeywordIndex.from_chunk_index(
            PROJECT_ROOT / "data" / "chunks" / "chunk_index.csv",
            PROJECT_ROOT / "data" / "chunks",
        )
        # Search a larger set if we need to filter by Act
        results = bm25_index.search(query_text, top_k=top_k * 4 if filter_act else top_k)

        filtered = []
        for item in results:
            text = item.get("text", "")
            if filter_act:
                act_lower = filter_act.lower()
                text_lower = text.lower()
                if "constitution" in act_lower and ("constitution" not in text_lower and not text_lower.startswith("10 ") and not text_lower.startswith("25 ") and "article" not in text_lower):
                    continue
                elif "penal code" in act_lower and ("penal code" not in text_lower and "ppc" not in text_lower):
                    continue
                elif "criminal procedure" in act_lower and ("criminal procedure" not in text_lower and "crpc" not in text_lower):
                    continue
            filtered.append({"text": text, "score": item.get("score", 0.0), "metadata": item.get("metadata", {})})
            if len(filtered) >= top_k:
                break

        return filtered
    except Exception:
        return []


def hybrid_retrieve(query_text: str, collection, embed_model, filter_act: str | None = None,
                    dense_top_k: int = 6, bm25_top_k: int = 6, final_top_k: int = 5,
                    dense_weight: float = 0.6, bm25_weight: float = 0.4, return_scores: bool = False):
    """Hybrid retrieval: merge dense + BM25 results via weighted score fusion.

    Dense similarity is converted from cosine distance (0=best, 1=worst) to a
    similarity score (1=best, 0=worst), then both scores are min-max normalized
    to [0,1] before weighted combination.
    """
    # 1. Dense retrieval (fetch more candidates for merging)
    dense_docs, dense_metas, dense_dists = retrieve_context(
        query_text, collection, embed_model, top_k=dense_top_k, filter_act=filter_act
    )
    # Convert distance to similarity: sim = 1 - dist
    dense_sims = [1.0 - d for d in dense_dists]

    # 2. BM25 retrieval
    bm25_results = retrieve_bm25_scored(query_text, filter_act=filter_act, top_k=bm25_top_k)

    # 3. Build candidate map keyed by doc text (deduplicated)
    candidates = {}  # doc_text -> {"dense_sim": float, "bm25_score": float}

    for doc, sim in zip(dense_docs, dense_sims):
        candidates[doc] = {"dense_sim": sim, "bm25_score": 0.0}

    for item in bm25_results:
        text = item["text"]
        if text in candidates:
            candidates[text]["bm25_score"] = item["score"]
        else:
            candidates[text] = {"dense_sim": 0.0, "bm25_score": item["score"]}

    if not candidates:
        return []

    # 4. Min-max normalize each score dimension to [0, 1]
    all_dense = [c["dense_sim"] for c in candidates.values()]
    all_bm25 = [c["bm25_score"] for c in candidates.values()]

    dense_min, dense_max = min(all_dense), max(all_dense)
    bm25_min, bm25_max = min(all_bm25), max(all_bm25)

    dense_range = dense_max - dense_min if dense_max != dense_min else 1.0
    bm25_range = bm25_max - bm25_min if bm25_max != bm25_min else 1.0

    # 5. Compute weighted fusion score
    scored = []
    for doc_text, scores in candidates.items():
        norm_dense = (scores["dense_sim"] - dense_min) / dense_range
        norm_bm25 = (scores["bm25_score"] - bm25_min) / bm25_range
        final_score = dense_weight * norm_dense + bm25_weight * norm_bm25
        scored.append((doc_text, final_score))

    # 6. Sort by final score descending, return top_k
    scored.sort(key=lambda x: x[1], reverse=True)
    if return_scores:
        return scored[:final_top_k]
    return [doc for doc, _ in scored[:final_top_k]]


def rerank_with_cross_encoder(query: str, candidates: list[str], top_k: int = 3) -> list[str]:
    """Re-rank candidate chunks using a cross-encoder model."""
    if not candidates:
        return []
    
    try:
        # Initialize the cross-encoder model (downloads on first use)
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # Prepare pairs for scoring
        pairs = [[query, doc] for doc in candidates]
        
        # Predict scores
        scores = cross_encoder.predict(pairs)
        
        # Sort candidates by score descending
        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k docs
        return [doc for doc, _ in scored[:top_k]]
    except Exception as e:
        print(f"[CROSS-ENCODER ERROR] Falling back to pre-reranked order: {e}", file=sys.stderr)
        return candidates[:top_k]


def build_rag_prompt(query_text: str, retrieved_docs: list[str], conversation_history: list[dict] | None = None, mode: str = "layman", chat_topic: str | None = None) -> str:
    """Format the final prompt for the LLM using the loaded prompt template."""
    truncated_docs = [doc[:1500] for doc in retrieved_docs]
    context_block = "\n\n---\n\n".join(truncated_docs)

    history_block = "None"
    if conversation_history:
        recent = conversation_history[-6:]
        history_lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:200]
            history_lines.append(f"{role}: {content}")
        history_block = "\n".join(history_lines)

    topic_block = ""
    if chat_topic and chat_topic.strip():
        topic_block = f"\nCHAT TOPIC CONSTRAINT: This conversation is focused on '{chat_topic.strip()}'. If the user's question is unrelated to this topic, politely redirect them back to it.\n"

    if mode.lower() == "advocate":
        template = load_advocate_prompt_template()
    else:
        template = load_prompt_template()

    return template.format(context=context_block, question=query_text, history=history_block, topic=topic_block)


import time

def generate_answer(prompt: str) -> str:
    """Send the final prompt to the Groq model and return the answer, with auto-retry and model fallback."""
    models_to_try = [LLM_MODEL, "llama-3.1-8b-instant"]
    last_exception = None
    for model in models_to_try:
        for attempt in range(2):
            try:
                completion = client_groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    temperature=0.1,
                    max_tokens=1024,
                )
                return completion.choices[0].message.content
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                if "429" in err_str or "rate_limit" in err_str or "tokens" in err_str:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    break
    if last_exception:
        raise last_exception
    raise RuntimeError("Rate limit exceeded")


def detect_language(query: str) -> str:
    """Detect if query is in Urdu/Roman Urdu or English."""
    if bool(re.search(r'[\u0600-\u06FF]', query)):
        return "urdu"
    roman_urdu_words = {"saza", "kia", "kya", "hai", "ha", "ki", "ka", "ko", "par", "me", "mein", "hun", "ho", "batao", "bataen", "hyn", "hain", "chori", "ziada"}
    q_words = set(re.findall(r'\b[a-z]+\b', query.lower()))
    if len(q_words.intersection(roman_urdu_words)) >= 2:
        return "urdu"
    return "english"


import csv

def detect_act_from_query(query: str) -> str | None:
    """Infer target Act from user query string if not explicitly passed."""
    q_lower = query.lower()
    if "crpc" in q_lower or "criminal procedure" in q_lower:
        return "Code of Criminal Procedure, 1898"
    elif "ppc" in q_lower or "penal code" in q_lower:
        return "Pakistan Penal Code, 1860"
    elif "constitution" in q_lower or "article" in q_lower:
        return "Constitution of Pakistan"
    return None


def extract_all_requested_statutes(query_text: str) -> list[tuple[str | None, str]]:
    """
    Extract all explicit section/article references from a query, e.g.:
    'PPC Section 379 and PPC Section 420 under CrPC Section 497' ->
    [('Pakistan Penal Code, 1860', '379'), ('Pakistan Penal Code, 1860', '420'), ('Code of Criminal Procedure, 1898', '497')].
    """
    q_lower = query_text.lower()
    found = []

    # 1. Matches like "ppc section 379", "crpc section 497", "constitution article 10"
    for m in re.finditer(r'\b(ppc|crpc|constitution)\s+(?:section|article)?\s*(\d+[a-z]?)\b', q_lower):
        act_key = m.group(1)
        sec = m.group(2).upper()
        act = "Code of Criminal Procedure, 1898" if act_key == "crpc" else ("Pakistan Penal Code, 1860" if act_key == "ppc" else "Constitution of Pakistan")
        found.append((act, sec))

    # 2. Matches like "section 379 ppc", "section 420", "article 10A"
    for m in re.finditer(r'\b(?:section|article)\s*(\d+[a-z]?)(?:\s*(ppc|crpc|constitution))?\b', q_lower):
        sec = m.group(1).upper()
        act_key = m.group(2)
        if act_key:
            act = "Code of Criminal Procedure, 1898" if act_key == "crpc" else ("Pakistan Penal Code, 1860" if act_key == "ppc" else "Constitution of Pakistan")
        else:
            sub = q_lower[max(0, m.start()-20):min(len(q_lower), m.end()+20)]
            if "ppc" in sub or "penal" in sub:
                act = "Pakistan Penal Code, 1860"
            elif "crpc" in sub or "procedure" in sub:
                act = "Code of Criminal Procedure, 1898"
            elif "constitution" in sub or "article" in m.group(0):
                act = "Constitution of Pakistan"
            else:
                act = None
        if sec:
            found.append((act, sec))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for ref in found:
        if ref not in seen:
            seen.add(ref)
            unique.append(ref)

    return unique


def resolve_alias_chunks(query_text: str) -> list[str]:
    """Check query against LEGAL_ALIASES and explicit section references, fetching exact chunks."""
    q_lower = query_text.lower().strip()
    chunks = []

    matched_refs = []
    # 1. Explicit statutory section references parsed from query
    explicit_refs = extract_all_requested_statutes(query_text)
    for act_name, sec_num in explicit_refs:
        if act_name:
            matched_refs.append((act_name, sec_num))
        else:
            # Bare section without act: get for all acts
            for a in ["Code of Criminal Procedure, 1898", "Pakistan Penal Code, 1860", "Constitution of Pakistan"]:
                matched_refs.append((a, sec_num))

    # 2. Check exact match first, then word-boundary regex match for alias keys
    if q_lower in LEGAL_ALIASES:
        matched_refs.extend(LEGAL_ALIASES[q_lower])
    else:
        for alias_key, refs in LEGAL_ALIASES.items():
            if len(alias_key) > 2 and re.search(r'\b' + re.escape(alias_key) + r'\b', q_lower):
                matched_refs.extend(refs)

    # Deduplicate
    seen = set()
    unique_refs = []
    for ref in matched_refs:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)

    for act_name, section_num in unique_refs:
        chunk = get_exact_chunk_by_statute(act_name, section_num)
        if chunk and chunk not in chunks:
            chunks.append(chunk)

    return chunks


def extract_requested_statute(query_text: str) -> tuple[str | None, str | None]:
    """Return the primary explicit section/article from a query."""
    explicit_refs = extract_all_requested_statutes(query_text)
    if explicit_refs:
        return explicit_refs[0]
    return detect_act_from_query(query_text), None


def get_all_acts_for_section(section_num: str) -> list[str]:
    """For a bare section number, find all Acts that contain that section."""
    ALL_ACTS = [
        "Code of Criminal Procedure, 1898",
        "Pakistan Penal Code, 1860",
        "Constitution of Pakistan",
    ]
    found_acts = []
    for act in ALL_ACTS:
        chunk = get_exact_chunk_by_statute(act, section_num)
        if chunk:
            found_acts.append(act)
    return found_acts


def get_exact_chunk_by_statute(target_act: str, target_sec: str) -> str | None:
    """Look up exact chunk text for given Act and Section/Article."""
    try:
        chunks_dir = PROJECT_ROOT / "data" / "chunks"
        sec_clean = target_sec.lower().strip()
        
        # 1. Direct filename check for Constitution & PPC
        if "constitution" in target_act.lower():
            fname = f"constitution_article_{sec_clean}_chunk_0.txt"
            fpath = chunks_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as handle:
                    return handle.read()

        elif "penal code" in target_act.lower() or "ppc" in target_act.lower():
            fname = f"ppc_section_{sec_clean}_chunk_0.txt"
            fpath = chunks_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as handle:
                    return handle.read()

        # 2. CSV index lookup
        csv_path = chunks_dir / "chunk_index.csv"
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    act = row.get("act_name", "").strip()
                    sec = row.get("section_article_number", "").strip().upper()
                    if act.lower() == target_act.lower() and sec == target_sec.upper():
                        chunk_file = chunks_dir / row["chunk_filename"]
                        if chunk_file.exists():
                            with open(chunk_file, "r", encoding="utf-8") as handle:
                                return handle.read()

        # 3. Header text scanning fallback
        for file in chunks_dir.glob("*.txt"):
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                header = [f.readline() for _ in range(6)]
                header_text = "".join(header).upper()
                target_str = f"SECTION: {target_sec.upper()}"
                target_str2 = f"SECTION/ARTICLE: {target_sec.upper()}"
                if target_str in header_text or target_str2 in header_text:
                    f.seek(0)
                    return f.read()

    except Exception as e:
        print(f"[EXACT MATCH LOOKUP ERROR] {e}", file=sys.stderr)
        
    return None


def translate_query_to_english(query: str) -> str:
    """Translates Urdu/Roman Urdu queries to English for better retrieval."""
    try:
        response = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",  # Ultra-fast model
            messages=[
                {"role": "system", "content": "You are a translation assistant. If the text is in Urdu or Roman Urdu, translate it to English. If it is already in English, return it exactly as is. ONLY output the English translation, no quotation marks or explanations."},
                {"role": "user", "content": query}
            ],
            temperature=0.1,
            max_tokens=60
        )
        return response.choices[0].message.content.strip(' "')
    except Exception as e:
        print(f"[QUERY TRANSLATION ERROR] {e}", file=sys.stderr)
        return query


def verify_urdu_answer(answer: str, question: str) -> bool:
    """Call Groq to verify that an Urdu answer is contextually accurate and not hallucinated.
    Also checks for script contamination (Devanagari/Hindi mixed in).
    Returns True if answer passes verification, False if it fails."""
    # Pre-check: Detect Devanagari (Hindi) script contamination
    devanagari_chars = sum(1 for c in answer if '\u0900' <= c <= '\u097F')
    if devanagari_chars > 3:
        print(f"[URDU VERIFY] Devanagari contamination detected ({devanagari_chars} chars)", file=sys.stderr)
        return False

    try:
        response = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": (
                    "You are a Pakistani legal fact-checker. You will be given a question and an Urdu answer about Pakistani law. "
                    "Check TWO things: "
                    "1. Whether the answer is contextually relevant and does not contain obvious factual errors about Pakistani law (PPC, CrPC, Constitution). "
                    "2. Whether the answer is written in proper Urdu Nastaliq script (NOT Hindi/Devanagari, NOT Cyrillic, NOT any other script). "
                    "Reply with ONLY 'PASS' if both checks pass, or 'FAIL' if either check fails. "
                    "No explanation, just PASS or FAIL."
                )},
                {"role": "user", "content": f"Question: {question[:300]}\n\nUrdu Answer: {answer[:800]}"}
            ],
            temperature=0.0,
            max_tokens=5
        )
        verdict = response.choices[0].message.content.strip().upper()
        return "FAIL" not in verdict
    except Exception as e:
        print(f"[URDU VERIFY ERROR] {e}", file=sys.stderr)
        return True  # On error, default to showing the answer


def answer_question(question: str, filter_act: str | None = None, n_results: int = 3, conversation_history: list[dict] | None = None, mode: str = "layman", on_stage=None, chat_topic: str | None = None) -> tuple[str, list[str], bool]:
    """Single question-to-answer function that combines retrieval and LLM generation.
    Returns (answer, retrieved_docs, urdu_verified) where urdu_verified is True if
    the Urdu answer passed verification (or the answer is in English).
    """
    def _stage(msg):
        if on_stage:
            on_stage(msg)

    # Short-circuit: skip retrieval entirely for conversational messages
    if is_conversational(question):
        _stage("Drafting answer...")
        final_prompt = build_rag_prompt(question, [], conversation_history, mode, chat_topic)
        answer = generate_answer(final_prompt)
        return answer, [], True

    lang = detect_language(question)
    if lang == "urdu":
        _stage("Translating query...")
        search_query = translate_query_to_english(question)
    else:
        search_query = question
    
    target_act, target_sec = extract_requested_statute(search_query)

    # Step 1a: Alias lookup — check query against LEGAL_ALIASES
    alias_chunks = resolve_alias_chunks(search_query)

    # Step 1b: Exact-match lookup for explicit section/article references
    exact_chunks = []
    if target_sec:
        if target_act:
            # Act is known — fetch that specific chunk
            chunk = get_exact_chunk_by_statute(target_act, target_sec)
            if chunk:
                exact_chunks.append(chunk)
        else:
            # Bare section number (e.g. "Section 497") — fetch from ALL matching Acts
            matching_acts = get_all_acts_for_section(target_sec)
            for act in matching_acts:
                chunk = get_exact_chunk_by_statute(act, target_sec)
                if chunk and chunk not in exact_chunks:
                    exact_chunks.append(chunk)

    filter_act = target_act or filter_act or detect_act_from_query(search_query)

    # Note: We no longer hardcode an out-of-scope refusal here.
    # The LLM's dynamic formatting rules handle conversational/unrelated queries naturally.

    db_path = PROJECT_ROOT / "data" / "chroma_db"
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_collection(name="law_collection")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    # Step 3: Hybrid retrieval — merge dense + BM25 with weighted score fusion
    _stage("Analyzing laws...")
    hybrid_scored = hybrid_retrieve(
        search_query, collection, embed_model,
        filter_act=filter_act,
        dense_top_k=max(n_results, 6),
        bm25_top_k=6,
        final_top_k=10,  # Fetch more for reranking
        return_scores=True
    )
    
    hybrid_docs = [doc for doc, score in hybrid_scored]

    # Step 4: Cross-encoder re-ranking (with latency shortcut)
    # If the top hybrid candidate has a dominant score margin (> 0.15) over the second,
    # skip the expensive cross-encoder step.
    if len(hybrid_scored) > 1 and (hybrid_scored[0][1] - hybrid_scored[1][1]) > 0.15:
        reranked_docs = hybrid_docs[:n_results]
    else:
        reranked_docs = rerank_with_cross_encoder(search_query, hybrid_docs, top_k=n_results)

    # Build final list: explicit section first (guaranteed slot), then alias chunks,
    # then reranked hybrid results, deduplicated
    all_docs = list(exact_chunks)  # exact section match always gets priority slot
    for c in alias_chunks:
        if c not in all_docs:
            all_docs.append(c)
    for doc in reranked_docs:
        if doc not in all_docs:
            all_docs.append(doc)

    # Cap at 3 chunks — exact_chunks guaranteed, remaining slots filled by alias+hybrid
    retrieved_docs = all_docs[:3]

    # Guardrail: Check if a specific Act was requested but no matching chunks were retrieved
    if filter_act and not retrieved_docs:
        # Keep this only if they explicitly demand a section from a specific act but it fails.
        # Otherwise, let it pass to LLM.
        pass

    final_prompt = build_rag_prompt(question, retrieved_docs, conversation_history, mode, chat_topic)
    _stage("Drafting answer...")
    answer = generate_answer(final_prompt)

    # If the answer is a refusal / out-of-scope response, return empty sources
    answer_lower = answer.lower()
    refusal_keywords = [
        "do not have sufficient information",
        "does not mention",
        "does not provide",
        "not mentioned",
        "no relevant information",
        "not explicitly stated",
        "not contained in the provided",
        "not provided in the given context",
    ]
    if REFUSAL_SENTENCE in answer or any(kw in answer_lower for kw in refusal_keywords):
        return answer, [], True

    # Urdu answer verification
    urdu_verified = True
    if lang == "urdu" and bool(re.search(r'[\u0600-\u06FF]', answer)):
        _stage("Verifying Urdu context...")
        urdu_verified = verify_urdu_answer(answer, question)

    return answer, retrieved_docs, urdu_verified


def run_rag_pipeline(query_text: str, filter_act: str | None = None, conversation_history: list[dict] | None = None, mode: str = "layman"):
    """Backward-compatible wrapper that keeps the existing test harness working."""
    print("\n=== RAG Pipeline Execution ===")
    print(f"[{mode.upper()} MODE]")
    print("[1] Retrieving legal context...")
    answer, retrieved_docs, _ = answer_question(query_text, filter_act=filter_act, conversation_history=conversation_history, mode=mode)
    print("[2] Prompt built and answer generated.")
    print("\n=== FINAL ANSWER ===")
    print(answer)
    print("====================")
    return answer, retrieved_docs


def generate_chat_title(user_message: str) -> str:
    """Generate a strict 3-4 word legal topic title from the first user message."""
    msg_clean = user_message.strip().lower()
    msg_no_punct = re.sub(r'[^\w\s]', '', msg_clean)
    greeting_prefixes = ("hi", "hello", "hey", "greetings", "thanks", "thank you", "assalam", "aoa", "good morning", "good evening", "how are you", "how is it going", "hows it going", "how it going")
    
    has_legal_kw = any(kw in msg_clean for kw in ["fir", "ppc", "crpc", "law", "bail", "theft", "murder", "section", "article", "court", "crime", "punishment", "police", "case", "rights"])
    
    # Check if message is a simple greeting or non-legal conversational phrase
    if not has_legal_kw and (msg_no_punct in greeting_prefixes or any(msg_no_punct.startswith(p) for p in greeting_prefixes) or len(msg_clean) <= 15):
        return "General Inquiry"

    try:
        response = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": (
                    "You generate ultra-short chat titles for Pakistani legal assistant queries. "
                    "If the user message is a greeting or non-legal question (e.g. 'Hi', 'How are you', 'Thanks'), output EXACTLY 'General Inquiry'. "
                    "Otherwise, generate an ultra-short title: exactly 3-4 words, title case, no punctuation, no quotes, no filler words like 'Chat' or 'Conversation'. "
                    "Focus strictly on Pakistani statutory law. Always use PPC for Pakistan Penal Code, CrPC for Code of Criminal Procedure, or Constitution. "
                    "Output ONLY the title, nothing else."
                )},
                {"role": "user", "content": user_message[:200]}
            ],
            temperature=0.1,
            max_tokens=12
        )
        title = response.choices[0].message.content.strip(' "\n')
        # Replace accidental IPC references
        title = re.sub(r'\bIPC\b', 'PPC', title, flags=re.IGNORECASE)
        words = title.split()
        return " ".join(words[:4]) if words else user_message[:30]
    except Exception as e:
        print(f"[TITLE GENERATION ERROR] {e}", file=sys.stderr)
        words = user_message.split()
        return " ".join(words[:4])


def run_logging_pipeline(questions: list[str], log_file: str | None = None, filter_act: str | None = None):
    """Run the pipeline over multiple questions and persist a structured JSON log."""
    LOG_DIR.mkdir(exist_ok=True)

    output_path = Path(log_file) if log_file else LOG_DIR / "pipeline_run_log.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for index, question in enumerate(questions, start=1):
        answer, retrieved_docs = answer_question(question, filter_act=filter_act)
        results.append(
            {
                "question_id": index,
                "question": question,
                "filter_act": filter_act,
                "answer": answer,
                "retrieved_chunk_count": len(retrieved_docs),
                "retrieved_chunks": retrieved_docs,
            }
        )

    payload = {
        "timestamp": datetime.now().isoformat(),
        "model": LLM_MODEL,
        "total_questions": len(questions),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    return payload


if __name__ == "__main__":
    sample_questions = [
        "What are the safeguards as to arrest and detention under Article 10?",
        "Does the Constitution prohibit forced labour and slavery?",
    ]
    run_logging_pipeline(sample_questions, filter_act="Constitution of Pakistan")
