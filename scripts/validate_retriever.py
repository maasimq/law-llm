import os
import chromadb
from sentence_transformers import SentenceTransformer

# Ahmad Rasheed (23L-0786) - Day 11 Work
# Define 10 test queries covering PPC, CrPC, and the Constitution
TEST_QUERIES = [
    # Pakistan Penal Code (PPC)
    "What is the punishment for theft?",
    "How is murder (Qatl-e-Amd) defined in the penal code?",
    "What are the exceptions to criminal defamation?",
    
    # Constitution of Pakistan, 1973
    "What are the fundamental rights regarding freedom of speech?",
    "Can a person be subjected to double jeopardy or retroactive punishment under the constitution?",
    "What are the rights regarding fair trial?",
    "What does the constitution say about slavery and forced labor?",
    
    # Code of Criminal Procedure (CrPC)
    "What is the procedure for police to arrest a person without a warrant?",
    "How is a First Information Report (FIR) registered?",
    "Under what circumstances can bail be granted in non-bailable offences?"
]

def run_retriever_validation():
    print("=== Retriever Validation Protocol ===")
    print("Initializing Vector DB and Embedding Model...\n")
    
    db_path = os.path.join("data", "chroma_db")
    if not os.path.exists(db_path):
        print(f"Error: ChromaDB path '{db_path}' not found. Ensure ingestion is completed.")
        return
        
    client = chromadb.PersistentClient(path=db_path)
    try:
        collection = client.get_collection(name="law_collection")
    except Exception as e:
        print(f"Collection not found: {e}")
        return
        
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    success_count = 0
    print("Starting validation of 10 test queries...\n")
    print("-" * 60)
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"Test Query {i}/10: '{query}'")
        query_embedding = model.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        retrieved_sources = []
        for meta in results['metadatas'][0]:
            act = meta.get('act_name', 'Unknown')
            sec = meta.get('section_article_number', 'Unknown')
            retrieved_sources.append(f"{act} - {sec}")
            
        print("Top 3 Retrieved Chunks:")
        for rank, source in enumerate(retrieved_sources, 1):
            print(f"  {rank}. {source}")
        
        print("-" * 60)

    print("\nValidation completed. Please manually review the relevancy of the retrieved sources.")

if __name__ == "__main__":
    run_retriever_validation()
