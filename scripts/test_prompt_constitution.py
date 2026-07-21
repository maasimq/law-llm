"""
Day 14 Checkpoint: Prompt Template Demo
=========================================
Tests the finalized prompt_template.txt by running 5 questions through the Groq LLM
WITH retrieved context from ChromaDB, demonstrating correct citation behaviour.
Saves output to logs/checkpoint7_prompt_demo.txt.
"""

import os
import csv
import json
import numpy as np
import chromadb
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH       = PROJECT_ROOT / "data"   / "chroma_db"
EMBEDDINGS_DIR = PROJECT_ROOT / "data"  / "embeddings"
TEMPLATE_FILE  = PROJECT_ROOT / "scripts" / "prompt_template.txt"
LOG_FILE       = PROJECT_ROOT / "logs"  / "checkpoint7_prompt_demo.txt"

MODEL_NAME = "llama-3.3-70b-versatile"

# 5 sample questions with their proxy embeddings (pre-saved .npy files)
SAMPLE_QA = [
    {
        "question": "What are the rights of an arrested person under the Constitution of Pakistan?",
        "proxy_npy": "constitution_article_10_chunk_0.npy",
        "filter": {"act_name": "Constitution of Pakistan"}
    },
    {
        "question": "Is forced labor permitted in Pakistan?",
        "proxy_npy": "constitution_article_11_chunk_0.npy",
        "filter": {"act_name": "Constitution of Pakistan"}
    },
    {
        "question": "What is the right to a fair trial under Pakistani law?",
        "proxy_npy": "constitution_article_10a_chunk_0.npy",
        "filter": {"act_name": "Constitution of Pakistan"}
    },
    {
        "question": "What does the Constitution say about the right to education?",
        "proxy_npy": "constitution_article_25a_chunk_0.npy",
        "filter": {"act_name": "Constitution of Pakistan"}
    },
    {
        "question": "Can a person be tried twice for the same offense in Pakistan?",
        "proxy_npy": "constitution_article_13_chunk_0.npy",
        "filter": {"act_name": "Constitution of Pakistan"}
    }
]


def load_template():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def retrieve_context(collection, proxy_npy, act_filter, n_results=3):
    emb_path = EMBEDDINGS_DIR / proxy_npy
    if not emb_path.exists():
        return "No context found."
    query_embedding = np.load(emb_path).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=act_filter
    )
    chunks = []
    for i in range(len(results["ids"][0])):
        meta    = results["metadatas"][0][i]
        doc_txt = results["documents"][0][i]
        article = meta.get("section_article_number", "Unknown")
        act     = meta.get("act_name", "Unknown Act")
        chunks.append(f"[{act}, Article {article}]\n{doc_txt.strip()}")
    return "\n\n---\n\n".join(chunks)


def ask_with_template(client, template, question, context):
    filled = template.replace("{context}", context).replace("{question}", question)
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a Pakistani Legal Assistant. Follow all instructions in the prompt exactly."},
            {"role": "user",   "content": filled}
        ],
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=600
    )
    return response.choices[0].message.content


def run():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set in .env")
        return

    client     = Groq(api_key=api_key)
    template   = load_template()
    chroma_cli = chromadb.PersistentClient(path=str(DB_PATH))
    collection = chroma_cli.get_collection("law_collection")

    print("=" * 60)
    print("DAY 14 CHECKPOINT: Prompt Template Demo")
    print(f"Model: {MODEL_NAME}")
    print("=" * 60)

    log_lines = [
        "Checkpoint 7: Prompt Template Demo",
        "====================================",
        f"Model:    {MODEL_NAME}",
        f"Template: {TEMPLATE_FILE}",
        ""
    ]

    for idx, item in enumerate(SAMPLE_QA, 1):
        question  = item["question"]
        proxy_npy = item["proxy_npy"]
        act_filter = item["filter"]

        print(f"\n--- Q{idx}: {question} ---")
        context = retrieve_context(collection, proxy_npy, act_filter)
        answer  = ask_with_template(client, template, question, context)

        print(f"Answer:\n{answer}\n")

        log_lines.append(f"Question {idx}: {question}")
        log_lines.append("")
        log_lines.append("Context retrieved:")
        for chunk in context.split("---"):
            log_lines.append("  " + chunk.strip()[:300])
        log_lines.append("")
        log_lines.append("Answer:")
        log_lines.append(answer)
        log_lines.append("")
        log_lines.append("-" * 60)
        log_lines.append("")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"[OK] Checkpoint 7 complete. Log saved to {LOG_FILE}")


if __name__ == "__main__":
    run()
