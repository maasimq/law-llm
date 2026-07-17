import os
import chromadb
from sentence_transformers import SentenceTransformer

def query_vector_database(query_text, n_results=3):
    print("Initializing ChromaDB Persistent Client...")
    db_path = os.path.join("data", "chroma_db")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=db_path)
    
    # Load the collection
    collection = client.get_collection(name="law_collection")
    print(f"Total documents in collection: {collection.count()}")
    
    # Load the embedding model (same one used for generating embeddings)
    print("Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    # Generate embedding for the query
    print(f"\nQuerying: '{query_text}'")
    query_embedding = model.encode(query_text).tolist()
    
    # Perform similarity search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    # Display the results
    print("\n=== SEARCH RESULTS ===")
    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        distance = results['distances'][0][i]
        metadata = results['metadatas'][0][i]
        
        print(f"\nResult {i+1}:")
        print(f"ID: {doc_id}")
        print(f"Act: {metadata['act_name']}, Article/Section: {metadata['section_article_number']}")
        print(f"Similarity Distance: {distance:.4f}")
        print(f"Snippet: {results['documents'][0][i][:200]}...")

if __name__ == "__main__":
    sample_query = "What are the fundamental rights of a citizen regarding arrest?"
    query_vector_database(sample_query)
