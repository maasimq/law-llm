"""
Supervisor Test Run Script
===========================
Runs 20 curated supervisor-level legal questions through the full RAG pipeline
(retrieval + prompt engineering + LLM generation) and logs each result in detail.
Results are saved to logs/supervisor_test_log.json for review.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import run_rag_pipeline

# 20 supervisor-level test questions across PPC, CrPC, and Constitution
SUPERVISOR_QUESTIONS = [
    # PPC (7 Questions)
    {"id": 1,  "category": "PPC",          "question": "What is the definition and punishment for murder under PPC?"},
    {"id": 2,  "category": "PPC",          "question": "What constitutes abetment of a crime under the Pakistan Penal Code?"},
    {"id": 3,  "category": "PPC",          "question": "What is the punishment for theft in Pakistan?"},
    {"id": 4,  "category": "PPC",          "question": "How does PPC define criminal breach of trust?"},
    {"id": 5,  "category": "PPC",          "question": "What are the penalties for forgery under the Pakistan Penal Code?"},
    {"id": 6,  "category": "PPC",          "question": "What is the right of private defence of the body under PPC?"},
    {"id": 7,  "category": "PPC",          "question": "What constitutes criminal intimidation and its punishment under PPC?"},
    # Constitution (7 Questions)
    {"id": 8,  "category": "Constitution", "question": "What rights does Article 9 of the Constitution of Pakistan guarantee?"},
    {"id": 9,  "category": "Constitution", "question": "What are the safeguards against arbitrary arrest under Article 10?"},
    {"id": 10, "category": "Constitution", "question": "What does the Constitution say about freedom of speech and expression?"},
    {"id": 11, "category": "Constitution", "question": "How does the Constitution protect against double jeopardy and retrospective punishment?"},
    {"id": 12, "category": "Constitution", "question": "What does Article 14 say about human dignity and privacy?"},
    {"id": 13, "category": "Constitution", "question": "What fundamental rights does the Constitution grant regarding freedom of association?"},
    {"id": 14, "category": "Constitution", "question": "What protection does the Constitution offer against forced labour?"},
    # CrPC (6 Questions)
    {"id": 15, "category": "CrPC",         "question": "When can a police officer make an arrest without a warrant under CrPC?"},
    {"id": 16, "category": "CrPC",         "question": "What is the procedure for registering an FIR under CrPC?"},
    {"id": 17, "category": "CrPC",         "question": "What are the conditions for granting bail in non-bailable offences?"},
    {"id": 18, "category": "CrPC",         "question": "What is the role of a magistrate during a criminal investigation?"},
    {"id": 19, "category": "CrPC",         "question": "How are search warrants issued and executed under CrPC?"},
    {"id": 20, "category": "CrPC",         "question": "What are the duties of a police officer during investigation of a cognizable offence?"},
]


def run_supervisor_tests():
    print("=" * 65)
    print("SUPERVISOR TEST RUN — 20 Legal Questions")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    results = []

    for item in SUPERVISOR_QUESTIONS:
        qid      = item["id"]
        category = item["category"]
        question = item["question"]

        print(f"\n[{qid:02d}/{len(SUPERVISOR_QUESTIONS)}] [{category}] {question}")

        try:
            answer, retrieved_docs = run_rag_pipeline(question)
            status = "success"
            print(f"   Chunks retrieved: {len(retrieved_docs)} | Answer length: {len(answer)} chars")
        except Exception as e:
            answer        = None
            retrieved_docs = []
            status        = f"error: {str(e)}"
            print(f"   ERROR: {e}")

        results.append({
            "id":              qid,
            "category":        category,
            "question":        question,
            "answer":          answer,
            "chunks_retrieved": len(retrieved_docs),
            "status":          status,
        })

    # Persist results
    log_dir = PROJECT_ROOT / "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = log_dir / "supervisor_test_log.json"

    output = {
        "timestamp":      datetime.now().isoformat(),
        "total":          len(SUPERVISOR_QUESTIONS),
        "successful":     sum(1 for r in results if r["status"] == "success"),
        "results":        results,
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print(f"Completed: {output['successful']}/{output['total']} runs successful.")
    print(f"Log saved to: {log_path}")
    print("=" * 65)


if __name__ == "__main__":
    run_supervisor_tests()
