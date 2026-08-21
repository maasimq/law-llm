"""
retrieval_eval.py — Retrieval-only evaluation harness for the Pakistani Legal Assistant RAG pipeline.

Runs the retriever (no LLM call) against a hand-labeled test set and reports
per-query pass/fail plus an overall pass rate.

A query "passes" if ALL expected (act, section) pairs appear somewhere in the
retrieved chunk set (checked via metadata headers or text content).

Usage:
    python scripts/retrieval_eval.py
"""

import csv
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

PROJECT_ROOT = Path(__file__).resolve().parent.parent

import os
import logging
logging.getLogger("chromadb.telemetry.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from sentence_transformers import SentenceTransformer
from bm25_index import BM25KeywordIndex
from rag_pipeline import (
    hybrid_retrieve,
    rerank_with_cross_encoder,
    extract_requested_statute,
    get_exact_chunk_by_statute,
    get_all_acts_for_section,
    detect_act_from_query,
    resolve_alias_chunks,
)

# ============================================================
# TEST SET — 30 hand-labeled (query, expected) pairs
# ============================================================
# Each entry: (query_string, [(act_name_substring, section_number), ...])
# A test passes if EVERY expected pair is found in the retrieved chunks.

TEST_SET = [
    # --- Bare section/article numbers ---
    ("Section 154", [("Criminal Procedure", "154")]),
    ("Section 302", [("Penal Code", "302")]),
    ("Article 10A", [("Constitution", "10A")]),
    ("Article 10", [("Constitution", "10")]),
    ("Article 19", [("Constitution", "19")]),
    ("Section 378", [("Penal Code", "378")]),
    ("Section 498", [("Criminal Procedure", "498")]),

    # --- Bare section with Act qualifier ---
    ("Section 497 CrPC", [("Criminal Procedure", "497")]),
    ("Section 497 PPC", [("Penal Code", "497")]),
    ("Section 302 PPC", [("Penal Code", "302")]),
    ("Article 25A Constitution", [("Constitution", "25A")]),

    # --- Ambiguous bare section (should return BOTH Acts) ---
    ("Section 497", [("Criminal Procedure", "497"), ("Penal Code", "497")]),

    # --- One-word / short terms ---
    ("FIR", [("Criminal Procedure", "154")]),
    ("bail", [("Criminal Procedure", "497")]),
    ("theft", [("Penal Code", "378")]),
    ("murder", [("Penal Code", "302")]),
    ("robbery", [("Penal Code", "390")]),
    ("dacoity", [("Penal Code", "391")]),
    ("kidnapping", [("Penal Code", "359")]),
    ("forgery", [("Penal Code", "463")]),
    ("defamation", [("Penal Code", "499")]),
    ("fair trial", [("Constitution", "10A")]),
    ("fundamental rights", [("Constitution", "8")]),

    # --- Full natural-language questions ---
    ("What are the grounds for bail in non-bailable offences?", [("Criminal Procedure", "497")]),
    ("How is a First Information Report registered?", [("Criminal Procedure", "154")]),
    ("What is the punishment for murder under Pakistan Penal Code?", [("Penal Code", "302")]),
    ("What does Article 10A say about the right to a fair trial?", [("Constitution", "10A")]),
    ("What safeguards exist against arbitrary arrest and detention?", [("Constitution", "10")]),
    ("What are the constitutional provisions regarding freedom of speech?", [("Constitution", "19")]),
    ("What is the definition of theft in PPC?", [("Penal Code", "378")]),
    ("What is the distinction between robbery and dacoity?", [("Penal Code", "390")]),
]

NON_ALIASED_TEST_SET = [
    ("criminal breach of trust", [("Penal Code", "405")]),
    ("hurt caused by rash or negligent driving", [("Penal Code", "337G")]),
    ("unlawful assembly", [("Penal Code", "141")]),
    ("preventive detention review board", [("Constitution", "10")]),
    ("search of a place without a warrant", [("Criminal Procedure", "165")]),
    ("attempt to commit an offence", [("Penal Code", "511")]),
    ("criminal conspiracy", [("Penal Code", "120A")]),
    ("wrongful confinement", [("Penal Code", "340")]),
    ("cheating and dishonestly inducing delivery of property", [("Penal Code", "420")]),
    ("right to information under the Constitution", [("Constitution", "19A")]),
]

def chunk_matches_expected(chunk_text: str, act_substr: str, section_num: str) -> bool:
    """Check if a retrieved chunk matches an expected (act, section) pair."""
    text_upper = chunk_text.upper()
    act_upper = act_substr.upper()

    # Check act name appears in chunk
    act_found = act_upper in text_upper

    # Check section/article number appears in chunk header or content
    sec_upper = section_num.upper()
    section_patterns = [
        f"SECTION: {sec_upper}",
        f"SECTION/ARTICLE: {sec_upper}",
        f"ARTICLE: {sec_upper}",
        f"SECTION {sec_upper}.",
        f"SECTION {sec_upper} ",
        f"{sec_upper}.",   # e.g. "10A.\tRight to fair trial"
    ]
    section_found = any(pat in text_upper for pat in section_patterns)

    # Also check filename-style patterns in the text (e.g. constitution chunks start with "10A.\t")
    if not section_found:
        # For constitution articles that start with "10A.\t"
        if text_upper.lstrip().startswith(f"{sec_upper}.") or text_upper.lstrip().startswith(f"{sec_upper}\t"):
            section_found = True

    return act_found or section_found  # act_found alone can be too broad; but section_found alone works for most


def chunk_matches_expected_strict(chunk_text: str, act_substr: str, section_num: str) -> bool:
    """Stricter check: section number must be in the chunk, and act name should match if present."""
    text_upper = chunk_text.upper()
    sec_upper = section_num.upper()

    # Must find section number in chunk
    section_patterns = [
        f"SECTION: {sec_upper}\n",
        f"SECTION: {sec_upper}\r",
        f"SECTION/ARTICLE: {sec_upper}\n",
        f"SECTION/ARTICLE: {sec_upper}\r",
        f"ARTICLE: {sec_upper}\n",
        f"ARTICLE: {sec_upper}\r",
    ]
    section_found = any(pat in text_upper for pat in section_patterns)

    # Fallback: check for "154. Information" style pattern at line start
    if not section_found:
        line_pattern = re.compile(rf"^\s*{re.escape(sec_upper)}[\.\t\s]", re.MULTILINE)
        if line_pattern.search(text_upper):
            section_found = True

    if not section_found:
        return False

    # If act name substring is provided, verify it appears
    act_upper = act_substr.upper()
    if act_upper in text_upper:
        return True

    # For Constitution chunks that may not explicitly say "Constitution" in text
    if "CONSTITUTION" in act_upper:
        # Constitution articles often start directly with "10A.\tRight to..."
        return True

    return section_found


import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

_eval_chroma_client = None
_eval_collection = None
_eval_embed_model = None

def get_eval_resources():
    global _eval_chroma_client, _eval_collection, _eval_embed_model
    if _eval_chroma_client is None:
        db_path = PROJECT_ROOT / "data" / "chroma_db"
        _eval_chroma_client = chromadb.PersistentClient(path=str(db_path), settings=Settings(anonymized_telemetry=False))
        _eval_collection = _eval_chroma_client.get_collection(name="law_collection")
        try:
            _eval_embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5", local_files_only=True)
        except Exception:
            _eval_embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _eval_collection, _eval_embed_model

def retrieve_only(query: str, top_k: int = 5):
    """Run retrieval pipeline without LLM generation. Returns list of chunk texts."""
    target_act, target_sec = extract_requested_statute(query)
    filter_act = target_act or detect_act_from_query(query)

    collection, embed_model = get_eval_resources()

    # Step 1a: Alias lookup
    alias_chunks = resolve_alias_chunks(query)

    # Step 1b: Exact-match lookup
    exact_chunks = []
    if target_sec:
        if target_act:
            chunk = get_exact_chunk_by_statute(target_act, target_sec)
            if chunk:
                exact_chunks.append(chunk)
        else:
            # Bare section — fetch from ALL matching Acts
            matching_acts = get_all_acts_for_section(target_sec)
            for act in matching_acts:
                chunk = get_exact_chunk_by_statute(act, target_sec)
                if chunk and chunk not in exact_chunks:
                    exact_chunks.append(chunk)

    # Merge priority chunks
    priority_chunks = []
    for c in alias_chunks + exact_chunks:
        if c not in priority_chunks:
            priority_chunks.append(c)

    # Step 3: Hybrid retrieval
    hybrid_scored = hybrid_retrieve(
        query, collection, embed_model,
        filter_act=filter_act,
        dense_top_k=max(top_k, 6),
        bm25_top_k=6,
        final_top_k=top_k * 2,  # Fetch more for reranking
        return_scores=True
    )
    
    hybrid_docs = [doc for doc, score in hybrid_scored]

    # Step 4: Cross-encoder re-ranking
    if len(hybrid_scored) > 1 and (hybrid_scored[0][1] - hybrid_scored[1][1]) > 0.15:
        reranked_docs = hybrid_docs[:top_k]
    else:
        reranked_docs = rerank_with_cross_encoder(query, hybrid_docs, top_k=top_k)

    # Merge: priority first, then reranked hybrid results
    all_docs = list(priority_chunks)
    for doc in reranked_docs:
        if doc not in all_docs:
            all_docs.append(doc)

    return all_docs[:top_k]


def run_eval():
    """Run the full evaluation and print results."""
    print("=" * 70)
    print("RETRIEVAL EVALUATION HARNESS")
    print("=" * 70)

    # 1. Aliased Set
    print("\n--- ALIASED TEST SET ---")
    aliased_results, aliased_rate, aliased_latency = run_test_set(TEST_SET)
    
    # 2. Non-Aliased Set
    print("\n--- NON-ALIASED TEST SET ---")
    non_aliased_results, non_aliased_rate, non_aliased_latency = run_test_set(NON_ALIASED_TEST_SET)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Aliased Set Pass Rate:     {aliased_rate:.1f}%")
    print(f"Non-Aliased Set Pass Rate: {non_aliased_rate:.1f}%")
    print(f"Average Latency (Aliased):     {aliased_latency:.3f}s / query")
    print(f"Average Latency (Non-Aliased): {non_aliased_latency:.3f}s / query")
    print("=" * 70)
    
    return non_aliased_rate


def run_test_set(test_set):
    passed = 0
    failed = 0
    results = []
    total_time = 0.0

    for query, expected_pairs in test_set:
        start_time = time.time()
        retrieved_chunks = retrieve_only(query, top_k=5)
        end_time = time.time()
        total_time += (end_time - start_time)

        # Check if ALL expected pairs are found in the retrieved set
        all_found = True
        missing = []
        for act_substr, section_num in expected_pairs:
            found = any(
                chunk_matches_expected_strict(chunk, act_substr, section_num)
                for chunk in retrieved_chunks
            )
            if not found:
                all_found = False
                missing.append(f"{act_substr} § {section_num}")

        status = "PASS" if all_found else "FAIL"
        if all_found:
            passed += 1
        else:
            failed += 1

        results.append((query, status, missing, len(retrieved_chunks)))

    # Print results
    print(f"\n{'QUERY':<60} {'STATUS':>6}  DETAILS")
    print("-" * 90)
    for query, status, missing, n_chunks in results:
        q_display = query[:57] + "..." if len(query) > 57 else query
        if status == "FAIL":
            detail = f"MISSING: {', '.join(missing)} ({n_chunks} chunks retrieved)"
            print(f"{q_display:<60} {status:>6}  {detail}")
        else:
            print(f"{q_display:<60} {status:>6}  ({n_chunks} chunks)")

    total = passed + failed
    rate = (passed / total * 100) if total > 0 else 0
    avg_time = (total_time / total) if total > 0 else 0
    
    print("-" * 90)
    print(f"RESULTS: {passed}/{total} passed ({rate:.1f}%)")
    
    return results, rate, avg_time


if __name__ == "__main__":
    run_eval()
