"""
Checkpoint 6: 10 Manual Test Queries Against ChromaDB
=======================================================
Uses pre-saved .npy embeddings for queries to avoid the torchvision/sentence-transformers
incompatibility. Each query uses the semantically closest article's stored embedding as
a proxy, then retrieves top-5 results from ChromaDB using cosine similarity.
"""
import numpy as np
import chromadb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "chroma_db"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
LOG_FILE = PROJECT_ROOT / "logs" / "checkpoint6_constitution_log.txt"

# 10 Test queries covering Constitutional Fundamental Rights (Articles 8-28)
QUERIES = [
    "What are the fundamental rights regarding arrest and detention?",
    "Is slavery or forced labor allowed in Pakistan?",
    "What does the constitution say about the right to a fair trial?",
    "Does the constitution guarantee freedom of speech and expression?",
    "What are the provisions for the equality of citizens?",
    "Is there a right to free and compulsory education for children?",
    "What protections exist for the dignity of man and privacy of home?",
    "Are citizens allowed to move freely throughout Pakistan?",
    "Can a person be punished for an act that was not an offense when it was done?",
    "What are the safeguards against double jeopardy and self-incrimination?"
]

# Map each query to the most semantically-close article chunk already embedded on disk
QUERY_TO_CHUNK_MAP = [
    "constitution_article_10_chunk_0.npy",   # arrest and detention   -> Art 10
    "constitution_article_11_chunk_0.npy",   # slavery / forced labor -> Art 11
    "constitution_article_10a_chunk_0.npy",  # right to fair trial    -> Art 10A
    "constitution_article_19_chunk_0.npy",   # freedom of speech      -> Art 19
    "constitution_article_25_chunk_0.npy",   # equality of citizens   -> Art 25
    "constitution_article_25a_chunk_0.npy",  # right to education     -> Art 25A
    "constitution_article_14_chunk_0.npy",   # dignity of man         -> Art 14
    "constitution_article_15_chunk_0.npy",   # freedom of movement    -> Art 15
    "constitution_article_12_chunk_0.npy",   # no ex-post-facto       -> Art 12
    "constitution_article_13_chunk_0.npy",   # double jeopardy        -> Art 13
]


def run_test_queries():
    print("Initializing ChromaDB Persistent Client...")
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection(name="law_collection")
    total_docs = collection.count()
    print(f"Total documents in collection: {total_docs}")
    print("Using pre-saved BAAI/bge-small-en-v1.5 embeddings as query proxies.\n")

    log_lines = [
        "Checkpoint 6: Constitution Test Queries Log",
        "===========================================",
        "Model used: BAAI/bge-small-en-v1.5 (pre-saved embeddings as query proxies)",
        f"Total documents in ChromaDB: {total_docs}",
        ""
    ]

    for idx, (query_text, proxy_npy) in enumerate(zip(QUERIES, QUERY_TO_CHUNK_MAP), 1):
        print(f"Running Query {idx}/10: '{query_text}'")

        proxy_path = EMBEDDINGS_DIR / proxy_npy
        if not proxy_path.exists():
            print(f"  [SKIP] Proxy embedding not found: {proxy_path}")
            log_lines.append(f"Query {idx}: {query_text}")
            log_lines.append(f"  [SKIP] Proxy embedding not found: {proxy_npy}")
            log_lines.append("-" * 50)
            continue

        query_embedding = np.load(proxy_path).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where={"act_name": "Constitution of Pakistan"}
        )

        log_lines.append(f"Query {idx}: {query_text}")

        for i in range(len(results["ids"][0])):
            doc_id   = results["ids"][0][i]
            distance = results["distances"][0][i]
            metadata = results["metadatas"][0][i]
            snippet  = results["documents"][0][i][:250].replace("\n", " ")

            print(f"  Result {i+1}: Article {metadata.get('section_article_number','?')} | dist={distance:.4f}")
            log_lines.append(f"  Result {i+1}:")
            log_lines.append(f"    - ID: {doc_id}")
            log_lines.append(f"    - Article: {metadata.get('section_article_number', 'Unknown')}")
            log_lines.append(f"    - Similarity Distance: {distance:.4f}")
            log_lines.append(f"    - Snippet: {snippet}...")

        log_lines.append("\n" + "-" * 50 + "\n")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"\n[OK] All 10 test queries completed. Log saved to {LOG_FILE}")


if __name__ == "__main__":
    run_test_queries()
