import os
import chromadb
from sentence_transformers import SentenceTransformer

# Retriever Validation Script
# Purpose: Tests whether the ChromaDB vector database retrieves
#          the correct legal chunks for a set of predefined queries.
# Each query is encoded into a vector and matched against the stored
# embeddings using cosine similarity. The top-3 results are printed
# with their Act name and Section/Article number for manual review.

# 10 test queries spanning all three legal sources
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
    """
    Loops through TEST_QUERIES, encodes each query using the same embedding
    model used during ingestion, queries ChromaDB for the top-3 nearest
    chunks, and prints the source (Act + Section) for manual relevancy review.
    """
    print("=== Retriever Validation Protocol ===")
    print("Initializing Vector DB and Embedding Model...\n")

    # Resolve path to the persistent ChromaDB directory
    db_path = os.path.join("data", "chroma_db")
    if not os.path.exists(db_path):
        print(f"Error: ChromaDB path '{db_path}' not found. Ensure ingestion is completed.")
        return

    # Connect to the persisted ChromaDB instance
    client = chromadb.PersistentClient(path=db_path)
    try:
        # Load the collection that was created during setup_chromadb.py
        collection = client.get_collection(name="law_collection")
    except Exception as e:
        print(f"Collection not found: {e}")
        return

    # Use the same model that was used to generate stored embeddings
    # to ensure vector space alignment during retrieval
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    print("Starting validation of 10 test queries...\n")
    print("-" * 60)

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"Test Query {i}/10: '{query}'")

        # BGE models require a prefix for retrieval queries
        prefixed_query = "Represent this sentence for searching relevant passages: " + query
        # Encode the query into a 384-dimensional vector
        query_embedding = model.encode(prefixed_query, normalize_embeddings=True).tolist()

        # Retrieve the top-3 most similar chunks from ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3  # Return top 3 nearest neighbours
        )

        # Extract Act name and Section/Article number from each result's metadata
        retrieved_sources = []
        for meta in results['metadatas'][0]:
            act = meta.get('act_name', 'Unknown')
            sec = meta.get('section_article_number', 'Unknown')
            retrieved_sources.append(f"{act} - {sec}")

        print("Top 3 Retrieved Chunks:")
        for rank, source in enumerate(retrieved_sources, 1):
            print(f"  {rank}. {source}")

        print("-" * 60)

    # Reviewer should check whether retrieved sources are relevant to each query
    print("\nValidation completed. Please manually review the relevancy of the retrieved sources.")


if __name__ == "__main__":
    run_retriever_validation()
