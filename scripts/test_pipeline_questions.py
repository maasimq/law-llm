"""
Pipeline Initial Run Test Script
=================================
Abdul Raheem (Day 15 Work)
Prepares a structured set of test questions covering PPC, CrPC, and Constitution,
executes initial runs against the full RAG pipeline, and logs results for review.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import run_rag_pipeline

# 15 Curated Test Questions covering PPC, CrPC, and Constitution
TEST_QUESTIONS = [
    # PPC Questions
    {"id": 1, "category": "PPC", "question": "What is the punishment for theft under the Pakistan Penal Code?"},
    {"id": 2, "category": "PPC", "question": "How is murder (Qatl-e-Amd) defined in the penal code?"},
    {"id": 3, "category": "PPC", "question": "What are the legal penalties for criminal breach of trust?"},
    {"id": 4, "category": "PPC", "question": "What constitutes the offence of criminal intimidation under PPC?"},
    {"id": 5, "category": "PPC", "question": "What is the punishment for forgery under Pakistan Penal Code?"},
    
    # Constitution Questions
    {"id": 6, "category": "Constitution", "question": "What fundamental rights does Article 9 of the Constitution protect?"},
    {"id": 7, "category": "Constitution", "question": "What are the safeguards as to arrest and detention under Article 10?"},
    {"id": 8, "category": "Constitution", "question": "Does the Constitution of Pakistan prohibit forced labor and slavery?"},
    {"id": 9, "category": "Constitution", "question": "What protection is provided against double jeopardy and retrospective punishment?"},
    {"id": 10, "category": "Constitution", "question": "What does the Constitution state regarding freedom of speech and expression?"},

    # CrPC Questions
    {"id": 11, "category": "CrPC", "question": "When can a police officer arrest a person without a warrant under CrPC?"},
    {"id": 12, "category": "CrPC", "question": "What is the legal procedure for registering a First Information Report (FIR)?"},
    {"id": 13, "category": "CrPC", "question": "What are the provisions regarding bail in non-bailable offences?"},
    {"id": 14, "category": "CrPC", "question": "What is the purpose and procedure of a search warrant under CrPC?"},
    {"id": 15, "category": "CrPC", "question": "What are the duties of an investigating officer during a police investigation?"}
]

def run_initial_pipeline_tests():
    print("=" * 65)
    print("DAY 15 — INITIAL PIPELINE TEST RUNS (Abdul Raheem)")
    print(f"Total Test Questions: {len(TEST_QUESTIONS)}")
    print("=" * 65)

    test_logs = []

    for item in TEST_QUESTIONS:
        qid = item["id"]
        cat = item["category"]
        qtext = item["question"]

        print(f"\n[{qid}/{len(TEST_QUESTIONS)}] [{cat}] Q: {qtext}")
        try:
            answer, retrieved_docs = run_rag_pipeline(qtext)
            print(f"   Response Length: {len(answer)} chars")
            print(f"   Retrieved Chunks: {len(retrieved_docs)}")

            test_logs.append({
                "question_id": qid,
                "category": cat,
                "question": qtext,
                "answer": answer,
                "retrieved_chunk_count": len(retrieved_docs),
                "status": "success"
            })
        except Exception as e:
            print(f"   ERROR: {e}")
            test_logs.append({
                "question_id": qid,
                "category": cat,
                "question": qtext,
                "answer": None,
                "retrieved_chunk_count": 0,
                "status": f"error: {str(e)}"
            })

    # Save log output
    os.makedirs(PROJECT_ROOT / "logs", exist_ok=True)
    log_file = PROJECT_ROOT / "logs" / "initial_pipeline_test_log.json"
    
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(TEST_QUESTIONS),
        "successful_runs": sum(1 for log in test_logs if log["status"] == "success"),
        "logs": test_logs
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print(f"Initial test runs completed. Log saved to: {log_file}")
    print("=" * 65)

if __name__ == "__main__":
    run_initial_pipeline_tests()
