import os
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "chroma_db"
LOG_FILE = PROJECT_ROOT / "logs" / "checkpoint6_constitution_log.txt"

def run_test_queries():
    print("Initializing ChromaDB Persistent Client...")
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection(name="law_collection")
    
    print(f"Total documents in collection: {collection.count()}")

    print("Loading embedding model BAAI/bge-small-en-v1.5...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    # 10 Test queries focused on the Constitution (Fundamental Rights, Articles 8-28)
    queries = [
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

    log_lines = [
        "Checkpoint 6: Constitution Test Queries Log",
        "===========================================",
        f"Model used: BAAI/bge-small-en-v1.5",
        ""
    ]

    for idx, query_text in enumerate(queries, 1):
        print(f"Running Query {idx}/10: '{query_text}'")
        query_embedding = model.encode(query_text, normalize_embeddings=True).tolist()
        
        # Querying top 5 results as requested
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where={"act_name": "Constitution of Pakistan"}  # Filter specifically for the Constitution
        )
        
        log_lines.append(f"Query {idx}: {query_text}")
        
        # Format the retrieved chunks
        for i in range(len(results['ids'][0])):
            doc_id = results['ids'][0][i]
            distance = results['distances'][0][i]
            metadata = results['metadatas'][0][i]
            snippet = results['documents'][0][i][:250].replace('\n', ' ')
            
            log_lines.append(f"  Result {i+1}:")
            log_lines.append(f"    - ID: {doc_id}")
            log_lines.append(f"    - Article: {metadata.get('section_article_number', 'Unknown')}")
            log_lines.append(f"    - Similarity Distance: {distance:.4f}")
            log_lines.append(f"    - Snippet: {snippet}...")
        log_lines.append("\n" + "-"*50 + "\n")

    # Save to logs directory
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"\n✅ All 10 test queries completed. Log saved to {LOG_FILE}")

if __name__ == "__main__":
    run_test_queries()
