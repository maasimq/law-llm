import os
import chromadb
from sentence_transformers import SentenceTransformer

from bm25_index import BM25KeywordIndex


def query_vector_database(query_text, n_results=3):
    print("Initializing ChromaDB Persistent Client...")
    db_path = os.path.join("data", "chroma_db")

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name="law_collection")
    print(f"Total documents in collection: {collection.count()}")

    print("Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    print(f"\nQuerying: '{query_text}'")
    query_embedding = model.encode(query_text).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    print("\n=== DENSE VECTOR RESULTS ===")
    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        distance = results['distances'][0][i]
        metadata = results['metadatas'][0][i]

        print(f"\nResult {i+1}:")
        print(f"ID: {doc_id}")
        print(f"Act: {metadata['act_name']}, Article/Section: {metadata['section_article_number']}")
        print(f"Similarity Distance: {distance:.4f}")
        print(f"Snippet: {results['documents'][0][i][:200]}...")

    print("\n=== BM25 KEYWORD RESULTS ===")
    index = BM25KeywordIndex.from_chunk_index(
        os.path.join("data", "chunks", "chunk_index.csv"),
        os.path.join("data", "chunks"),
    )
    bm25_results = index.search(query_text, top_k=n_results)
    for i, result in enumerate(bm25_results, 1):
        metadata = result.get("metadata", {})
        print(f"\nKeyword Result {i}:")
        print(f"ID: {result['id']}")
        print(f"Act: {metadata.get('act_name', 'Unknown')}, Article/Section: {metadata.get('section_article_number', 'Unknown')}")
        print(f"BM25 Score: {result['score']:.4f}")
        print(f"Snippet: {result['text'][:200]}...")

if __name__ == "__main__":
    sample_query = "What are the fundamental rights of a citizen regarding arrest?"
    query_vector_database(sample_query)
