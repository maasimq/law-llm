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
    "theft": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379")],
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
INSTRUCTIONS:
1. Answer using only the provided context.
2. Cite the exact Act name and Section/Article number.
3. Explain complex terms simply.
CONVERSATION HISTORY (if any):
{history}
CONTEXT:
{context}
USER QUESTION:
{question}
ANSWER:"""


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


def build_rag_prompt(query_text: str, retrieved_docs: list[str], conversation_history: list[dict] | None = None, mode: str = "layman") -> str:
    """Format the final prompt for the LLM using the loaded prompt template.
    
    Args:
        query_text: The user's current question.
        retrieved_docs: List of retrieved chunk texts.
        conversation_history: Optional list of recent messages [{"role": ..., "content": ...}]
                             to provide conversational context to the LLM.
        mode: "layman" or "advocate" to switch formatting instructions.
    """
    # Truncate each document to ~3000 characters (approx 750 tokens)
    # With 3 chunks max, total context stays under ~2250 tokens + prompt,
    # well within Groq free-tier 12,000 TPM limit.
    truncated_docs = [doc[:3000] for doc in retrieved_docs]
    context_block = "\n\n---\n\n".join(truncated_docs)
    
    # Build conversation history string (last 5 messages for context)
    history_block = "None"
    if conversation_history:
        recent = conversation_history[-10:]  # Last 5 Q&A pairs (10 messages)
        history_lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate each historical message to keep prompt within limits
            content = msg["content"][:500]
            history_lines.append(f"{role}: {content}")
        history_block = "\n".join(history_lines)
    
    if mode.lower() == "advocate":
        template = load_advocate_prompt_template()
    else:
        template = load_prompt_template()
        
    return template.format(context=context_block, question=query_text, history=history_block)


def generate_answer(prompt: str) -> str:
    """Send the final prompt to the Groq model and return the answer."""
    completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=LLM_MODEL,
        temperature=0.1,
        max_tokens=1024,
    )
    return completion.choices[0].message.content


def is_out_of_scope_question(question: str, filter_act: str | None = None) -> bool:
    """Return True when a constitution-specific pipeline is asked a non-constitutional question."""
    if filter_act != "Constitution of Pakistan":
        return False

    normalized = " ".join((question or "").lower().split())

    constitutional_terms = [
        "article",
        "constitution",
        "fundamental rights",
        "fundamental right",
        "right to",
        "rights",
        "liberty",
        "arrest",
        "detention",
        "slavery",
        "forced labour",
        "forced labor",
        "fair trial",
        "property",
        "education",
        "religion",
        "speech",
        "expression",
        "association",
        "union",
        "assembly",
        "movement",
        "privacy",
        "dignity",
        "equality",
        "public places",
        "discrimination",
        "compulsory deprivation",
        "religious purposes",
        "citizen",
        "double jeopardy",
        "self-incrimination",
        "tried twice",
    ]

    out_of_scope_terms = [
        "tax rate",
        "tax",
        "rental income",
        "trademark",
        "register",
        "registration",
        "criminal penalty",
        "criminal penalties",
        "theft",
        "ppc",
        "companies act",
        "passport",
        "advertising",
        "marriage",
        "partnership",
        "voter registration",
        "gasoline",
        "company",
        "corporate",
        "business",
        "licence",
        "license",
        "bail",
        "fir",
        "contract",
        "statute",
        "law governs",
        "income",
        "revenue",
    ]

    if any(term in normalized for term in constitutional_terms):
        return False

    return any(term in normalized for term in out_of_scope_terms)


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


def resolve_alias_chunks(query_text: str) -> list[str]:
    """Check query against LEGAL_ALIASES and fetch exact chunks for any matches."""
    q_lower = query_text.lower().strip()
    chunks = []

    # Check exact match first, then substring match for multi-word aliases
    matched_refs = []
    if q_lower in LEGAL_ALIASES:
        matched_refs = LEGAL_ALIASES[q_lower]
    else:
        # Check if any alias key appears as a standalone term in the query
        for alias_key, refs in LEGAL_ALIASES.items():
            if len(alias_key) > 2 and alias_key in q_lower:
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
    """
    Detect explicit section/article queries e.g.
    'Article 10A', 'Article 10', 'Section 497', 'Section 302 PPC', '497 CrPC'.
    Returns (act_name, section_article_number).
    act_name is None when the query has a bare section number with no Act qualifier.
    """
    q_lower = query_text.lower()
    act = detect_act_from_query(query_text)
    
    # Check for Article XX or Article XXA
    art_match = re.search(r'article\s*(\d+[a-z]?)', q_lower)
    if art_match:
        sec = art_match.group(1).upper()
        return "Constitution of Pakistan", sec

    # Check for Section XXX or Section XXXA
    sec_match = re.search(r'section\s*(\d+[a-z]?)', q_lower)
    if sec_match:
        sec = sec_match.group(1).upper()
        return act, sec  # act may be None for bare "Section 154"

    # Check for number + Act e.g. "497 crpc" or "302 ppc"
    num_act_match = re.search(r'(\d+[a-z]?)\s*(crpc|ppc)', q_lower)
    if num_act_match:
        sec = num_act_match.group(1).upper()
        act_key = num_act_match.group(2)
        target_act = "Code of Criminal Procedure, 1898" if act_key == "crpc" else "Pakistan Penal Code, 1860"
        return target_act, sec

    return act, None


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


def answer_question(question: str, filter_act: str | None = None, n_results: int = 3, conversation_history: list[dict] | None = None, mode: str = "layman") -> tuple[str, list[str]]:
    """Single question-to-answer function that combines retrieval and LLM generation."""
    target_act, target_sec = extract_requested_statute(question)

    # Step 1a: Alias lookup — check query against LEGAL_ALIASES
    alias_chunks = resolve_alias_chunks(question)

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

    # Merge alias + exact match (alias first, then exact, deduplicated)
    priority_chunks = []
    for c in alias_chunks + exact_chunks:
        if c not in priority_chunks:
            priority_chunks.append(c)

    filter_act = target_act or filter_act or detect_act_from_query(question)

    # Note: We no longer hardcode an out-of-scope refusal here.
    # The LLM's dynamic formatting rules handle conversational/unrelated queries naturally.

    db_path = PROJECT_ROOT / "data" / "chroma_db"
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_collection(name="law_collection")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    # Step 3: Hybrid retrieval — merge dense + BM25 with weighted score fusion
    hybrid_scored = hybrid_retrieve(
        question, collection, embed_model,
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
        reranked_docs = rerank_with_cross_encoder(question, hybrid_docs, top_k=n_results)

    # Build final list: priority chunks first, then reranked hybrid results, deduplicated
    all_docs = list(priority_chunks)
    for doc in reranked_docs:
        if doc not in all_docs:
            all_docs.append(doc)

    # Cap at 3 chunks total to stay under Groq free-tier TPM limits
    retrieved_docs = all_docs[:3]

    # Guardrail: Check if a specific Act was requested but no matching chunks were retrieved
    if filter_act and not retrieved_docs and not detect_language(question) == "urdu":
        # Keep this only if they explicitly demand a section from a specific act but it fails.
        # Otherwise, let it pass to LLM.
        pass

    final_prompt = build_rag_prompt(question, retrieved_docs, conversation_history, mode)
    answer = generate_answer(final_prompt)

    # If the answer is a refusal / out-of-scope response, return empty sources so no irrelevant citation cards render
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
        return answer, []

    return answer, retrieved_docs


def run_rag_pipeline(query_text: str, filter_act: str | None = None, conversation_history: list[dict] | None = None, mode: str = "layman"):
    """Backward-compatible wrapper that keeps the existing test harness working."""
    print("\n=== RAG Pipeline Execution ===")
    print(f"[{mode.upper()} MODE]")
    print("[1] Retrieving legal context...")
    answer, retrieved_docs = answer_question(query_text, filter_act=filter_act, conversation_history=conversation_history, mode=mode)
    print("[2] Prompt built and answer generated.")
    print("\n=== FINAL ANSWER ===")
    print(answer)
    print("====================")
    return answer, retrieved_docs


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
