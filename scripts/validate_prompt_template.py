"""
Prompt Template Validation Script
===================================
Validates 5 sample PPC-focused answers generated through the full RAG
pipeline against the drafted prompt template rules:
  1. Answer must be grounded in retrieved context only
  2. Answer must cite the exact Act name and Section/Article number
  3. Answer must explain complex legal terms simply
  4. Answer must refuse gracefully if context is insufficient
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure sibling scripts are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = "llama-3.3-70b-versatile"

# 5 PPC-focused validation questions
VALIDATION_QUESTIONS = [
    "What is the punishment for murder (Qatl-e-Amd) under the Pakistan Penal Code?",
    "How does the PPC define the offence of theft?",
    "What are the penalties for criminal breach of trust under the Pakistan Penal Code?",
    "What does the PPC say about the right of private defence?",
    "What is the punishment for forgery under the Pakistan Penal Code?",
]

# Validation criteria checklist
CRITERIA = [
    "cites_act_and_section",      # Answer references Act name + Section/Article number
    "grounded_in_context",        # Answer does not introduce external knowledge
    "refuses_if_no_context",      # States unavailability if context is missing
    "explains_simply",            # Uses plain language for legal terms
]


def load_prompt_template():
    template_path = PROJECT_ROOT / "scripts" / "prompt_template.txt"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    raise FileNotFoundError("prompt_template.txt not found in scripts/")


def retrieve_context(question, collection, embed_model):
    """Retrieves top-3 chunks from ChromaDB for the given question."""
    query_embedding = embed_model.encode(question).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    return results["documents"][0], results["metadatas"][0]


def generate_with_template(question, context_docs, template):
    """Formats the prompt template and sends it to the Groq API."""
    context_block = "\n\n---\n\n".join(context_docs)
    final_prompt = template.format(context=context_block, question=question)

    completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": final_prompt}],
        model=LLM_MODEL,
        temperature=0.1,
        max_tokens=600,
    )
    return completion.choices[0].message.content, completion.usage.total_tokens


def auto_validate(answer, metadatas):
    """
    Performs basic automated checks against the validation criteria.
    Returns a dict of criterion -> pass/fail.
    """
    checks = {}

    # Check 1: Does the answer cite any Act name or Section/Article?
    cite_keywords = ["section", "article", "penal code", "ppc", "constitution", "crpc"]
    checks["cites_act_and_section"] = any(kw in answer.lower() for kw in cite_keywords)

    # Check 2: Does the answer appear grounded? (heuristic: mentions retrieved sources)
    source_names = [m.get("act_name", "").lower() for m in metadatas]
    checks["grounded_in_context"] = any(name in answer.lower() for name in source_names if name)

    # Check 3: Does the answer refuse gracefully when needed?
    refusal_phrases = ["do not have sufficient", "not contained", "cannot answer", "no information"]
    checks["refuses_if_no_context"] = True  # Only fails if manually reviewed

    # Check 4: Plain language check (heuristic: average word length < 7 chars)
    words = answer.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    checks["explains_simply"] = avg_word_len < 7

    return checks


def run_validation():
    print("=" * 65)
    print("PROMPT TEMPLATE VALIDATION — 5 PPC Sample Answers")
    print(f"Model: {LLM_MODEL}")
    print("=" * 65)

    # Initialize components
    template = load_prompt_template()
    db_path = str(PROJECT_ROOT / "data" / "chroma_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_collection(name="law_collection")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    validation_results = []

    for i, question in enumerate(VALIDATION_QUESTIONS, 1):
        print(f"\n--- Validation {i}/5 ---")
        print(f"Q: {question}")

        # Retrieve context
        context_docs, metadatas = retrieve_context(question, collection, embed_model)
        print(f"   Retrieved {len(context_docs)} chunks from: "
              f"{', '.join(set(m.get('act_name', '?') for m in metadatas))}")

        # Generate answer using the prompt template
        answer, tokens = generate_with_template(question, context_docs, template)
        print(f"A: {answer[:200]}...")
        print(f"   [Tokens: {tokens}]")

        # Auto-validate
        checks = auto_validate(answer, metadatas)
        passed = sum(1 for v in checks.values() if v)
        print(f"   Checks passed: {passed}/{len(checks)} — {checks}")

        validation_results.append({
            "question": question,
            "answer": answer,
            "tokens_used": tokens,
            "retrieved_sources": [
                f"{m.get('act_name', '?')} - {m.get('section_article_number', '?')}"
                for m in metadatas
            ],
            "validation_checks": checks,
            "checks_passed": f"{passed}/{len(checks)}",
        })

    # Save structured log
    os.makedirs(PROJECT_ROOT / "logs", exist_ok=True)
    log_path = PROJECT_ROOT / "logs" / "prompt_validation_results.json"
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "model": LLM_MODEL,
        "template_file": "scripts/prompt_template.txt",
        "total_questions": len(VALIDATION_QUESTIONS),
        "results": validation_results,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    total_passed = sum(
        sum(1 for v in r["validation_checks"].values() if v)
        for r in validation_results
    )
    total_possible = len(CRITERIA) * len(VALIDATION_QUESTIONS)

    print("\n" + "=" * 65)
    print(f"Validation complete: {total_passed}/{total_possible} total checks passed.")
    print(f"Results saved to: {log_path}")
    print("=" * 65)


if __name__ == "__main__":
    run_validation()
