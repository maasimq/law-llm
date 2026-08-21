import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import logging
logging.getLogger("chromadb.telemetry.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer, CrossEncoder

from bm25_index import BM25KeywordIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
LLM_FAST_MODEL = os.getenv("LLM_FAST_MODEL", "openai/gpt-oss-20b")
REFUSAL_SENTENCE = "I do not have sufficient information in the provided legal text to answer this question."

# ============================================================
# SINGLETON IN-MEMORY MODEL & DB CACHE (Prevents per-query disk reloads)
# ============================================================
_chroma_client = None
_law_collection = None
_caselaw_collection = None
_embed_model = None
_cross_encoder = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        db_path = PROJECT_ROOT / "data" / "chroma_db"
        _chroma_client = chromadb.PersistentClient(path=str(db_path), settings=Settings(anonymized_telemetry=False))
    return _chroma_client

def get_law_collection():
    global _law_collection
    if _law_collection is None:
        _law_collection = get_chroma_client().get_collection(name="law_collection")
    return _law_collection

def get_caselaw_collection():
    global _caselaw_collection
    if _caselaw_collection is None:
        _caselaw_collection = get_chroma_client().get_collection(name="caselaw_collection")
    return _caselaw_collection

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            _embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5", local_files_only=True)
        except Exception:
            _embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _embed_model

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", local_files_only=True)
        except Exception:
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder

# ============================================================
# LEGAL ALIASES — map common terms/shorthand to exact (Act, Section) references
# ============================================================
LEGAL_ALIASES = {
    # --- Police & FIR ---
    "fir": [("Code of Criminal Procedure, 1898", "154")],
    "first information report": [("Code of Criminal Procedure, 1898", "154")],
    "second fir": [("Code of Criminal Procedure, 1898", "154"), ("Code of Criminal Procedure, 1898", "161")],
    "fir draft": [("Code of Criminal Procedure, 1898", "154"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "392")],
    "fir application": [("Code of Criminal Procedure, 1898", "154")],
    "draft fir": [("Code of Criminal Procedure, 1898", "154")],
    "justice of peace": [("Code of Criminal Procedure, 1898", "22A"), ("Code of Criminal Procedure, 1898", "22B")],
    "22-a": [("Code of Criminal Procedure, 1898", "22A"), ("Code of Criminal Procedure, 1898", "22B")],
    "quashment": [("Code of Criminal Procedure, 1898", "561-A")],
    "561-a": [("Code of Criminal Procedure, 1898", "561-A")],

    # --- Bail & Incarceration ---
    "bail": [("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "498")],
    "pre-arrest bail": [("Code of Criminal Procedure, 1898", "498")],
    "post-arrest bail": [("Code of Criminal Procedure, 1898", "497")],
    "statutory bail": [("Code of Criminal Procedure, 1898", "497")],
    "cancellation of bail": [("Code of Criminal Procedure, 1898", "497")],
    "bail petition": [("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "498")],

    # --- Homicide & Murder ---
    "murder": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "murdered": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "qatl": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "qatl-i-amd": [("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "qisas": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "304")],
    "diyat": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "338E")],
    "tazir": [("Pakistan Penal Code, 1860", "302")],
    "homicide": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "kill": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "killed": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "attempted murder": [("Pakistan Penal Code, 1860", "324")],
    "attempt to murder": [("Pakistan Penal Code, 1860", "324")],
    "punishment for murder": [("Pakistan Penal Code, 1860", "302")],
    "saza": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "392"), ("Pakistan Penal Code, 1860", "420")],
    "punishment": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "392"), ("Pakistan Penal Code, 1860", "420")],
    "surrender": [("Constitution of Pakistan", "10A"), ("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "498")],
    "accused rights": [("Constitution of Pakistan", "10"), ("Constitution of Pakistan", "10A")],

    # --- Financial & Cheque Crimes ---
    "cheque": [("Pakistan Penal Code, 1860", "489F")],
    "dishonored cheque": [("Pakistan Penal Code, 1860", "489F")],
    "dishonoured cheque": [("Pakistan Penal Code, 1860", "489F")],
    "bounced cheque": [("Pakistan Penal Code, 1860", "489F")],
    "cheque bounce": [("Pakistan Penal Code, 1860", "489F")],
    "489-f": [("Pakistan Penal Code, 1860", "489F")],
    "489f": [("Pakistan Penal Code, 1860", "489F")],
    "cheating": [("Pakistan Penal Code, 1860", "415"), ("Pakistan Penal Code, 1860", "420")],
    "fraud": [("Pakistan Penal Code, 1860", "415"), ("Pakistan Penal Code, 1860", "420")],
    "forgery": [("Pakistan Penal Code, 1860", "463"), ("Pakistan Penal Code, 1860", "464"), ("Pakistan Penal Code, 1860", "468"), ("Pakistan Penal Code, 1860", "471")],

    # --- Religious Offences & Toheen-e-Risalat ---
    "blasphemy": [("Pakistan Penal Code, 1860", "295C"), ("Pakistan Penal Code, 1860", "295A"), ("Code of Criminal Procedure, 1898", "156A")],
    "toheen e risalat": [("Pakistan Penal Code, 1860", "295C"), ("Code of Criminal Procedure, 1898", "156A")],
    "toheen-e-risalat": [("Pakistan Penal Code, 1860", "295C"), ("Code of Criminal Procedure, 1898", "156A")],
    "295-c": [("Pakistan Penal Code, 1860", "295C"), ("Code of Criminal Procedure, 1898", "156A")],
    "295c": [("Pakistan Penal Code, 1860", "295C"), ("Code of Criminal Procedure, 1898", "156A")],
    "sp investigation": [("Code of Criminal Procedure, 1898", "156A")],

    # --- Property Crimes ---
    "theft": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "steal": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "steals": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "stolen": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "stole": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "robbery": [("Pakistan Penal Code, 1860", "390"), ("Pakistan Penal Code, 1860", "392")],
    "dacoity": [("Pakistan Penal Code, 1860", "391"), ("Pakistan Penal Code, 1860", "395")],
    "stolen property": [("Pakistan Penal Code, 1860", "411")],

    # --- Bodily Hurt & General Exceptions ---
    "hurt": [("Pakistan Penal Code, 1860", "332"), ("Pakistan Penal Code, 1860", "337")],
    "private defence": [("Pakistan Penal Code, 1860", "96"), ("Pakistan Penal Code, 1860", "97"), ("Pakistan Penal Code, 1860", "100")],
    "self defence": [("Pakistan Penal Code, 1860", "96"), ("Pakistan Penal Code, 1860", "97"), ("Pakistan Penal Code, 1860", "100")],
    "kidnapping": [("Pakistan Penal Code, 1860", "359"), ("Pakistan Penal Code, 1860", "360")],
    "abduction": [("Pakistan Penal Code, 1860", "362")],
    "defamation": [("Pakistan Penal Code, 1860", "499"), ("Pakistan Penal Code, 1860", "500")],
    "adultery": [("Pakistan Penal Code, 1860", "497")],
    "case brief": [("Pakistan Penal Code, 1860", "302"), ("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "154")],

    # --- Constitutional Rights ---
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
    "rash driving": [("Pakistan Penal Code, 1860", "279"), ("Pakistan Penal Code, 1860", "320"), ("Pakistan Penal Code, 1860", "337G")],
    "negligent driving": [("Pakistan Penal Code, 1860", "279"), ("Pakistan Penal Code, 1860", "320"), ("Pakistan Penal Code, 1860", "337G")],
    "criminal conspiracy": [("Pakistan Penal Code, 1860", "120A"), ("Pakistan Penal Code, 1860", "120B")],
    "conspiracy": [("Pakistan Penal Code, 1860", "120A"), ("Pakistan Penal Code, 1860", "120B")],
    "harbouring": [("Pakistan Penal Code, 1860", "212"), ("Pakistan Penal Code, 1860", "216")],
    "harboring": [("Pakistan Penal Code, 1860", "212"), ("Pakistan Penal Code, 1860", "216")],
    "screening offender": [("Pakistan Penal Code, 1860", "201")],
    "hiding crime": [("Pakistan Penal Code, 1860", "201"), ("Pakistan Penal Code, 1860", "202")],

    # --- Urdu Aliases (Bilingual Support) ---
    "ایف آئی آر": [("Code of Criminal Procedure, 1898", "154")],
    "دوسری ایف آئی آر": [("Code of Criminal Procedure, 1898", "154"), ("Code of Criminal Procedure, 1898", "161")],
    "درخواست": [("Code of Criminal Procedure, 1898", "154")],
    "ضمانت": [("Code of Criminal Procedure, 1898", "497"), ("Code of Criminal Procedure, 1898", "498")],
    "قبل از گرفتاری": [("Code of Criminal Procedure, 1898", "498")],
    "بعد از گرفتاری": [("Code of Criminal Procedure, 1898", "497")],
    "چوری": [("Pakistan Penal Code, 1860", "378"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "380")],
    "قتل": [("Pakistan Penal Code, 1860", "299"), ("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "قتل عمد": [("Pakistan Penal Code, 1860", "300"), ("Pakistan Penal Code, 1860", "302")],
    "قصاص": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "304")],
    "دیت": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "338E")],
    "تعزیر": [("Pakistan Penal Code, 1860", "302")],
    "سزا": [("Pakistan Penal Code, 1860", "302"), ("Pakistan Penal Code, 1860", "379"), ("Pakistan Penal Code, 1860", "392")],
    "ڈکیتی": [("Pakistan Penal Code, 1860", "391"), ("Pakistan Penal Code, 1860", "395")],
    "لوٹ مار": [("Pakistan Penal Code, 1860", "390"), ("Pakistan Penal Code, 1860", "392")],
    "اغوا": [("Pakistan Penal Code, 1860", "359"), ("Pakistan Penal Code, 1860", "360")],
    "جعلسازی": [("Pakistan Penal Code, 1860", "463"), ("Pakistan Penal Code, 1860", "464")],
    "چیک": [("Pakistan Penal Code, 1860", "489F")],
    "چیک باؤنس": [("Pakistan Penal Code, 1860", "489F")],
    "توہین رسالت": [("Pakistan Penal Code, 1860", "295C"), ("Code of Criminal Procedure, 1898", "156A")],
    "توہین مذہب": [("Pakistan Penal Code, 1860", "295A"), ("Pakistan Penal Code, 1860", "295C")],
    "بنیادی حقوق": [("Constitution of Pakistan", "8")],
    "منصفانہ مقدمہ": [("Constitution of Pakistan", "10A")],
    "گرفتاری": [("Constitution of Pakistan", "10"), ("Code of Criminal Procedure, 1898", "54")],
    "آزادی اظہار": [("Constitution of Pakistan", "19")],
    "تعلیم کا حق": [("Constitution of Pakistan", "25A")],
    "مساوات": [("Constitution of Pakistan", "25")],
    "دھوکہ": [("Pakistan Penal Code, 1860", "415"), ("Pakistan Penal Code, 1860", "420")],
    "کوئش": [("Code of Criminal Procedure, 1898", "561-A")],
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
        cross_encoder = get_cross_encoder()
        pairs = [[query, doc] for doc in candidates]
        scores = cross_encoder.predict(pairs)
        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]
    except Exception as e:
        print(f"[CROSS-ENCODER ERROR] Falling back to pre-reranked order: {e}", file=sys.stderr)
        return candidates[:top_k]


CASE_LAW_CITATION_REGEX = re.compile(r'\b(19\d\d|20\d\d)\s+(SCMR|PLD|PCrLJ|CLC|MLD|YLR)\s+(\d+)\b', re.IGNORECASE)


def retrieve_case_precedents(query_text: str, n_results: int = 2) -> list[dict]:
    """Retrieve relevant Pakistani judicial precedents from ChromaDB 'caselaw_collection'."""
    try:
        collection = get_caselaw_collection()
    except Exception:
        return []

    exact_matches = []
    citation_match = CASE_LAW_CITATION_REGEX.search(query_text)
    if citation_match:
        year, journal, page = citation_match.groups()
        target_citation = f"{year} {journal.upper()} {page}"
        try:
            results = collection.get(where={"citation": target_citation})
            if results and results.get("metadatas"):
                for meta in results["metadatas"]:
                    exact_matches.append(meta)
        except Exception:
            pass

    semantic_matches = []
    try:
        embed_model = get_embed_model()
        query_emb = embed_model.encode([query_text], normalize_embeddings=True).tolist()
        results = collection.query(
            query_embeddings=query_emb,
            n_results=max(n_results * 2, 4)
        )
        if results and results.get("metadatas") and results["metadatas"][0]:
            for meta in results["metadatas"][0]:
                if meta not in exact_matches and meta not in semantic_matches:
                    semantic_matches.append(meta)
    except Exception as e:
        print(f"[CASELAW QUERY ERROR] {e}", file=sys.stderr)

    all_cases = exact_matches + semantic_matches
    return all_cases[:n_results]


def filter_cited_cases(answer: str, retrieved_cases: list[dict]) -> list[dict]:
    """Return cases that were actually relevant or cited in the LLM response."""
    if not retrieved_cases:
        return []
    
    ans_lower = answer.lower()
    cited = []
    for c in retrieved_cases:
        cit = c.get("citation", "").lower()
        title_words = c.get("case_title", "").lower().split(" v. ")
        petitioner = title_words[0].strip() if title_words else ""
        
        if (cit and cit in ans_lower) or (petitioner and len(petitioner) > 4 and petitioner in ans_lower) or ("scmr" in ans_lower or "pld" in ans_lower or "pcrlj" in ans_lower or "precedent" in ans_lower or "نظیر" in ans_lower or "عدالتی" in ans_lower):
            cited.append(c)
            
    if not cited and retrieved_cases:
        keywords = ["bail", "murder", "fir", "cheque", "delay", "warrant", "497", "302", "154", "489-f", "ضمانت", "قتل", "ایف آئی آر"]
        if any(kw in ans_lower for kw in keywords):
            cited = retrieved_cases[:1]
        
    return cited


def build_rag_prompt(query_text: str, retrieved_docs: list[str], conversation_history: list[dict] | None = None, mode: str = "layman", chat_topic: str | None = None, case_precedents: list[dict] | None = None) -> str:
    """Format the final prompt for the LLM using the loaded prompt template."""
    truncated_docs = [doc[:1500] for doc in retrieved_docs]
    context_block = "\n\n---\n\n".join(truncated_docs)

    if case_precedents:
        case_lines = []
        for c in case_precedents:
            case_lines.append(
                f"[JUDICIAL PRECEDENT / CASE LAW]\n"
                f"Citation: {c.get('citation')}\n"
                f"Case Title: {c.get('case_title')} ({c.get('court')}, {c.get('year')})\n"
                f"Applicable Statutes: {c.get('statutes_cited')}\n"
                f"Legal Principle (Ratio Decidendi): {c.get('ratio_decidendi')}\n"
                f"Urdu Principle: {c.get('urdu_ratio', '')}\n"
                f"Facts Summary: {c.get('facts_summary')}\n"
                f"Court Ruling: {c.get('disposition')}"
            )
        context_block = context_block + "\n\n=== RELEVANT JUDICIAL PRECEDENTS (CASE LAW) ===\n\n" + "\n\n---\n\n".join(case_lines)

    history_block = "None"
    if conversation_history:
        recent = conversation_history[-6:]
        history_lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:200]
            history_lines.append(f"{role}: {content}")
    topic_block = ""
    if chat_topic and chat_topic.strip():
        topic_block = f"\nCHAT TOPIC CONSTRAINT: This conversation is focused on '{chat_topic.strip()}'. If the user's question is unrelated to this topic, politely redirect them back to it.\n"

    lang = detect_language(query_text)
    if lang == "urdu":
        topic_block += "\n\nCRITICAL LANGUAGE MANDATE: The user query is in Urdu / Roman Urdu. You MUST write your entire response body in formal Pakistani Urdu script (اردو نستعلیق). Every explanation sentence must be in Urdu.\n"
    else:
        topic_block += "\n\nCRITICAL LANGUAGE MANDATE: The user query is in English. You MUST write your entire response in English.\n"

    if mode.lower() == "advocate":
        template = load_advocate_prompt_template()
    else:
        template = load_prompt_template()

    return template.format(context=context_block, question=query_text, history=history_block, topic=topic_block)


import time

def generate_answer(prompt: str) -> str:
    """Send the final prompt to the Groq model and return the answer, with auto-retry and model fallback."""
    models_to_try = [
        ("qwen/qwen3.6-27b", 6000),
        ("groq/compound", 6000),
        ("openai/gpt-oss-20b", 3000),
    ]
    last_exception = None
    for model, max_tok in models_to_try:
        call_kwargs = {
            "messages": [{"role": "user", "content": prompt}],
            "model": model,
            "temperature": 0.1,
            "max_tokens": max_tok,
        }
        if "qwen" in model or "gpt-oss" in model:
            call_kwargs["reasoning_format"] = "hidden"

        for attempt in range(2):
            try:
                completion = client_groq.chat.completions.create(**call_kwargs)
                choice = completion.choices[0]
                finish_reason = getattr(choice, "finish_reason", None)
                raw_text = choice.message.content or ""
                raw_text = raw_text.replace('\u202f', ' ').replace('\xa0', ' ')
                
                # Robust cleaning of <think> tags (both complete and unclosed)
                if "</think>" in raw_text:
                    cleaned_text = re.sub(r'<think>[\s\S]*?</think>', '', raw_text).strip()
                else:
                    cleaned_text = re.sub(r'<think>[\s\S]*$', '', raw_text).strip()

                # If finish_reason indicates token limit exhaustion and output is too short/empty, try fallback
                if finish_reason == "length" and len(cleaned_text) < 100:
                    continue

                if len(cleaned_text) > 30:
                    return cleaned_text
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                if "tokens per day" in err_str or "tpd" in err_str:
                    break
                elif "413" in err_str:
                    if call_kwargs["max_tokens"] > 2500:
                        call_kwargs["max_tokens"] = 2000
                        continue
                    break
                elif "429" in err_str or "rate_limit" in err_str or "tokens" in err_str:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    break
    if last_exception:
        raise last_exception
    raise RuntimeError("Service temporarily unavailable")


def is_conversational(query: str) -> bool:
    """Detect if a user prompt is purely conversational (greeting, thanks, identity) rather than a legal question."""
    q_clean = re.sub(r'[^\w\s]', '', query.strip().lower())
    greetings = {"hi", "hello", "hey", "greetings", "thanks", "thank you", "assalam", "aoa", "good morning", "good evening", "how are you", "who are you", "help", "kya haal hai", "salam"}
    legal_keywords = {"fir", "ppc", "crpc", "law", "bail", "theft", "murder", "section", "article", "court", "crime", "punishment", "police", "case", "rights", "chori", "saza", "qanoon", "adawlat", "judge", "constitution"}
    
    words = set(q_clean.split())
    if any(kw in q_clean for kw in legal_keywords):
        return False
    if q_clean in greetings or any(q_clean.startswith(g + " ") for g in greetings):
        return True
    if len(words) <= 3 and words.intersection(greetings):
        return True
    return False


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
    models_to_try = ["qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
    for model in models_to_try:
        try:
            call_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a translation assistant. If the text is in Urdu or Roman Urdu, translate it to English. If it is already in English, return it exactly as is. ONLY output the English translation, no quotation marks or explanations."},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
            if "qwen" in model or "gpt-oss" in model:
                call_kwargs["reasoning_format"] = "hidden"
            response = client_groq.chat.completions.create(**call_kwargs)
            raw = response.choices[0].message.content or ""
            if "</think>" in raw:
                cleaned = re.sub(r'<think>[\s\S]*?</think>', '', raw).strip(' "\n.')
            else:
                cleaned = re.sub(r'<think>[\s\S]*$', '', raw).strip(' "\n.')
            if cleaned:
                return cleaned
        except Exception:
            continue
    return query


def verify_and_correct_urdu_answer(answer: str, question: str, retrieved_docs: list[str] | None = None) -> tuple[str, bool]:
    """Call Groq API to verify, fact-check, and correct the Urdu legal response before showing to the user.
    Ensures:
    1. Legal accuracy against Pakistani statutory law (PPC, CrPC, Constitution).
    2. Proper formal Urdu Nastaliq vocabulary (eliminates Hindi/Devanagari idioms and unnatural grammar).
    3. Retains structured headings, bullet points, and citations.
    Returns (corrected_answer, is_verified).
    """
    if not answer or not bool(re.search(r'[\u0600-\u06FF]', answer)):
        return answer, True

    devanagari_chars = sum(1 for c in answer if '\u0900' <= c <= '\u097F')
    
    context_summary = ""
    if retrieved_docs:
        context_summary = "\n\n".join(retrieved_docs[:2])

    system_prompt = (
        "You are an expert Pakistani Legal Fact-Checker and Urdu Legal Editor. "
        "Review and correct the drafted Urdu response for a Pakistani legal assistant before it is shown to the user. "
        "Output ONLY the direct verified answer. Do NOT generate internal reasoning or think blocks. "
        "\nYOUR TASKS:\n"
        "1. FACT-CHECK: Ensure all cited statutory sections (PPC, CrPC, Constitution) and legal explanations are accurate and match Pakistani law. "
        "2. LANGUAGE CORRECTION: Ensure formal, grammatically correct Pakistani Urdu in authentic Nastaliq vocabulary. "
        "   - Eliminate any Hindi words, Devanagari characters, awkward machine translations, or grammatical errors. "
        "   - Strictly eliminate hybrid transliteration artifacts (e.g. '(مurder)', '(کُتل عمد)', '(مُرڈر)') and replace them with standard Pakistani Urdu legal terminology (e.g. 'قتلِ عمد', 'مقدمہ', 'سزا', 'ضمانت'). "
        "   - Ensure all Urdu section references are properly formatted (e.g. 'دفعہ 302 تعزیراتِ پاکستان (PPC)', 'آرٹیکل 10A آئینِ پاکستان'). "
        "3. FORMAT: Maintain clear markdown formatting, bullet points, and section citation headers. "
        "4. OUTPUT: Output ONLY the verified and corrected Urdu text. Do NOT add any preamble, conversational remarks, or explanation."
    )

    user_content = f"User Question: {question}\n\nDraft Urdu Answer:\n{answer}"
    if context_summary:
        user_content = f"Statutory Reference Context:\n{context_summary[:1200]}\n\n" + user_content

    models_to_try = ["qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
    for model in models_to_try:
        try:
            call_kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.1,
                "max_tokens": 8192
            }
            if "qwen" in model or "gpt-oss" in model:
                call_kwargs["reasoning_format"] = "hidden"
            response = client_groq.chat.completions.create(**call_kwargs)
            raw_c = response.choices[0].message.content or ""
            if "</think>" in raw_c:
                cleaned_c = re.sub(r'<think>[\s\S]*?</think>', '', raw_c).strip()
            else:
                cleaned_c = re.sub(r'<think>[\s\S]*$', '', raw_c).strip()
            if cleaned_c and len(cleaned_c) > 40:
                corr_devanagari = sum(1 for c in cleaned_c if '\u0900' <= c <= '\u097F')
                # Safety check: ensure verification output isn't truncated compared to original answer
                if corr_devanagari <= 2 and len(cleaned_c) >= len(answer) * 0.6:
                    return cleaned_c, True
        except Exception:
            continue
    return answer, True


def verify_urdu_answer(answer: str, question: str) -> bool:
    """Backward-compatible boolean check."""
    _, is_valid = verify_and_correct_urdu_answer(answer, question)
    return is_valid


def answer_question(question: str, filter_act: str | None = None, n_results: int = 3, conversation_history: list[dict] | None = None, mode: str = "layman", on_stage=None, chat_topic: str | None = None) -> tuple[str, list[str], bool, list[dict]]:
    """Single question-to-answer function that combines statutory retrieval, case law retrieval, and LLM generation.
    Returns (answer, retrieved_docs, urdu_verified, case_precedents).
    """
    def _stage(msg):
        if on_stage:
            on_stage(msg)

    # Short-circuit: skip retrieval entirely for conversational messages
    if is_conversational(question):
        _stage("Drafting answer...")
        final_prompt = build_rag_prompt(question, [], conversation_history, mode, chat_topic)
        answer = generate_answer(final_prompt)
        return answer, [], True, []

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

    collection = get_law_collection()
    embed_model = get_embed_model()

    # Step 3: Hybrid retrieval — merge dense + BM25 with weighted score fusion
    _stage("Analyzing laws & judicial precedents...")
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
    if len(hybrid_scored) > 1 and (hybrid_scored[0][1] - hybrid_scored[1][1]) > 0.15:
        reranked_docs = hybrid_docs[:n_results]
    else:
        reranked_docs = rerank_with_cross_encoder(search_query, hybrid_docs, top_k=n_results)

    # Build final list: explicit section first (guaranteed slot), then alias chunks,
    # then reranked hybrid results, deduplicated
    all_docs = list(exact_chunks)
    for c in alias_chunks:
        if c not in all_docs:
            all_docs.append(c)
    for doc in reranked_docs:
        if doc not in all_docs:
            all_docs.append(doc)

    retrieved_docs = all_docs[:3]

    # Step 5: Case Law / Judicial Precedents Retrieval
    case_precedents = retrieve_case_precedents(search_query, n_results=2)

    final_prompt = build_rag_prompt(question, retrieved_docs, conversation_history, mode, chat_topic, case_precedents=case_precedents)
    _stage("Drafting legal response...")
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
        return answer, [], True, []

    # Urdu answer verification & correction via API (ONLY for Urdu queries)
    urdu_verified = True
    if lang == "urdu":
        _stage("Verifying & refining Urdu context...")
        answer, urdu_verified = verify_and_correct_urdu_answer(answer, question, retrieved_docs)

    return answer, retrieved_docs, urdu_verified, case_precedents


def run_rag_pipeline(query_text: str, filter_act: str | None = None, conversation_history: list[dict] | None = None, mode: str = "layman", chat_topic: str | None = None, *args, **kwargs):
    """Backward-compatible wrapper that keeps the existing test harness working."""
    if not chat_topic:
        chat_topic = kwargs.get("topic") or kwargs.get("chat_topic")
    print("\n=== RAG Pipeline Execution ===")
    print(f"[{mode.upper()} MODE]")
    print("[1] Retrieving legal context & case precedents...")
    res = answer_question(query_text, filter_act=filter_act, conversation_history=conversation_history, mode=mode, chat_topic=chat_topic)
    answer, retrieved_docs = res[0], res[1]
    print("[2] Prompt built and answer generated.")
    print("\n=== FINAL ANSWER ===")
    print(answer)
    print("====================")
    return answer, retrieved_docs


def generate_chat_title(user_message: str = "", chat_topic: str | None = None, *args, **kwargs) -> str:
    """Generate a strict 2-3 word legal topic title based on topic and first user prompt."""
    if not chat_topic and len(args) > 0:
        chat_topic = args[0]
    if not chat_topic:
        chat_topic = kwargs.get("topic") or kwargs.get("chat_topic")

    msg_clean = user_message.strip() if user_message else ""
    topic_clean = str(chat_topic).strip() if chat_topic else ""

    # Parse fallback combined string if passed as single arg "Topic: Prompt"
    if ":" in msg_clean and not topic_clean:
        parts = msg_clean.split(":", 1)
        topic_clean = parts[0].strip()
        msg_clean = parts[1].strip()

    if not msg_clean and topic_clean:
        words = topic_clean.split()
        return " ".join(words[:3]).title()

    msg_no_punct = re.sub(r'[^\w\s]', '', msg_clean.lower())
    greeting_prefixes = ("hi", "hello", "hey", "greetings", "thanks", "thank you", "assalam", "aoa", "good morning", "good evening", "how are you", "how is it going", "hows it going", "how it going")
    
    has_legal_kw = any(kw in msg_clean.lower() for kw in ["fir", "ppc", "crpc", "law", "bail", "theft", "murder", "section", "article", "court", "crime", "punishment", "police", "case", "rights"])
    
    if not has_legal_kw and not topic_clean and (msg_no_punct in greeting_prefixes or any(msg_no_punct.startswith(p) for p in greeting_prefixes) or len(msg_clean) <= 15):
        return "General Inquiry"

    prompt_content = ""
    if topic_clean:
        prompt_content += f"Topic: {topic_clean}\n"
    if msg_clean:
        prompt_content += f"User Question: {msg_clean[:250]}"

    models_to_try = [LLM_FAST_MODEL, "qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
    for m in models_to_try:
        try:
            call_kwargs = {
                "model": m,
                "messages": [
                    {"role": "system", "content": (
                        "You generate ultra-short chat titles for Pakistani legal assistant queries. "
                        "Generate an ultra-short title based on the Topic and User Question provided. "
                        "CRITICAL: The title MUST be EXACTLY 2 to 3 words maximum. Never exceed 3 words. "
                        "Use Title Case, no punctuation, no quotes, no filler words like 'Chat' or 'Conversation' or 'Overview' or 'Application'. "
                        "Focus strictly on Pakistani statutory law. Always use PPC for Pakistan Penal Code, CrPC for Code of Criminal Procedure, or Constitution. "
                        "Output ONLY the 2-3 word title, nothing else."
                    )},
                    {"role": "user", "content": prompt_content}
                ],
                "temperature": 0.1,
                "max_tokens": 60
            }
            if "qwen" in m or "gpt-oss" in m:
                call_kwargs["reasoning_format"] = "hidden"
            response = client_groq.chat.completions.create(**call_kwargs)
            title = response.choices[0].message.content or ""
            title = title.strip(' "\n.')
            if "</think>" in title:
                title = re.sub(r'<think>[\s\S]*?</think>', '', title).strip()
            else:
                title = re.sub(r'<think>[\s\S]*$', '', title).strip()
            title = re.sub(r'\bIPC\b', 'PPC', title, flags=re.IGNORECASE)
            words = title.split()
            if words and len(words) <= 4:
                return " ".join(words[:3]).title()
        except Exception:
            continue

    # Intelligent legal keyword fallback if LLM is unreachable
    combined_text = f"{topic_clean} {msg_clean}".lower()
    sec_match = re.search(r'section\s*(\d+[a-z]?)', combined_text) or re.search(r'(\d+[a-z]?)\s*(ppc|crpc)', combined_text)
    law_code = "PPC" if "ppc" in combined_text else ("CrPC" if "crpc" in combined_text else "")
    
    if "fir" in combined_text and sec_match:
        return f"FIR Section {sec_match.group(1).upper()}"
    elif "fir" in combined_text:
        return "FIR Application"
    elif "bail" in combined_text and sec_match:
        return f"Bail Section {sec_match.group(1).upper()}"
    elif "bail" in combined_text:
        return "Bail Petition"
    elif "robbery" in combined_text or "392" in combined_text:
        return "Robbery Section 392"
    elif "theft" in combined_text or "379" in combined_text:
        return "Theft Section 379"
    elif "murder" in combined_text or "302" in combined_text:
        return "Murder Section 302"
    elif sec_match:
        return f"Section {sec_match.group(1).upper()} {law_code}".strip()
    
    words = [w for w in combined_text.split() if w not in ["draft", "a", "formal", "application", "to", "the", "for", "under", "in"]]
    return " ".join(words[:3]).title() if words else "Legal Inquiry"


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
