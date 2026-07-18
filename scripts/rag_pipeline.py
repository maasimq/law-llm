import os
import chromadb
from sentence_transformers import SentenceTransformer

from bm25_index import BM25KeywordIndex


def build_rag_prompt(query_text, retrieved_docs):
    """
    Constructs a prompt for the LLM using the retrieved context.
    """
    context = "\n\n---\n\n".join(retrieved_docs)
    
    prompt = f"""You are a helpful and knowledgeable legal AI assistant specializing in the law of Pakistan (Constitution, PPC, CrPC).
Use the following pieces of retrieved legal context to answer the user's question. 
If the answer is not contained in the context, say "I do not have enough information in my legal database to answer this question." Do not hallucinate laws.

Context:
{context}

Question: {query_text}

Answer:"""
    return prompt

def run_rag_pipeline(query_text):
    print("=== RAG Pipeline Execution ===")

    # 1. Retrieval Phase
    print("[1] Initializing Vector DB and Embedding Model...")
    db_path = os.path.join("data", "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name="law_collection")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    print(f"[2] Encoding Query: '{query_text}'")
    query_embedding = model.encode(query_text).tolist()

    print("[3] Searching Vector DB for relevant legal context...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    dense_docs = results['documents'][0]

    print("[3b] Building BM25 keyword index over chunk corpus...")
    bm25_index = BM25KeywordIndex.from_chunk_index(
        os.path.join("data", "chunks", "chunk_index.csv"),
        os.path.join("data", "chunks"),
    )
    bm25_results = bm25_index.search(query_text, top_k=3)
    keyword_docs = [item["text"] for item in bm25_results]

    retrieved_docs = dense_docs + keyword_docs
    retrieved_docs = list(dict.fromkeys(retrieved_docs))[:6]
    
    # 2. Augmentation Phase
    print("[4] Augmenting prompt with retrieved context (Prompt Engineering)...")
    final_prompt = build_rag_prompt(query_text, retrieved_docs)
    
    # 3. Generation Phase
    print("\n[5] Generated LLM Prompt (Ready to be sent to HuggingFace/Local LLM):\n")
    print("==================================================================")
    print(final_prompt)
    print("==================================================================")
    
    # NOTE: The actual LLM call (e.g. Llama-3, Mistral, or OpenAI API) will be integrated here next.
    # response = llm.generate(final_prompt)
    # return response

if __name__ == "__main__":
    sample_question = "What are the fundamental rights regarding arrest?"
    run_rag_pipeline(sample_question)
