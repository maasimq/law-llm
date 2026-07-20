import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

from bm25_index import BM25KeywordIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = "llama-3.3-70b-versatile"

def load_prompt_template():
    template_path = PROJECT_ROOT / "scripts" / "prompt_template.txt"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Fallback template
    return """You are a Legal Assistant specializing in Pakistani Law.
INSTRUCTIONS: Answer based ONLY on the provided context. Cite the exact Act and Section/Article. Explain simply.
CONTEXT:
{context}
USER QUESTION:
{question}
ANSWER:"""

def build_rag_prompt(query_text, retrieved_docs):
    """
    Constructs a prompt for the LLM using the retrieved context and the prompt template.
    """
    context = "\n\n---\n\n".join(retrieved_docs)
    template = load_prompt_template()
    prompt = template.format(context=context, question=query_text)
    return prompt

def generate_answer(prompt):
    chat_completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=LLM_MODEL,
        temperature=0.1,
        max_tokens=1024,
    )
    return chat_completion.choices[0].message.content

def run_rag_pipeline(query_text, filter_act=None):
    print("\n=== RAG Pipeline Execution ===")

    # 1. Retrieval Phase
    print("[1] Initializing Vector DB and Embedding Model...")
    db_path = os.path.join(PROJECT_ROOT, "data", "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name="law_collection")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    print(f"[2] Encoding Query: '{query_text}'")
    query_embedding = model.encode(query_text).tolist()

    print("[3] Searching Vector DB for relevant legal context...")
    
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": 3
    }
    if filter_act:
        query_params["where"] = {"act_name": filter_act}
        
    results = collection.query(**query_params)

    dense_docs = results['documents'][0]
    
    # Add BM25 context (Hybrid search simulation)
    try:
        bm25_index = BM25KeywordIndex.from_chunk_index(
            os.path.join(PROJECT_ROOT, "data", "chunks", "chunk_index.csv"),
            os.path.join(PROJECT_ROOT, "data", "chunks"),
        )
        bm25_results = bm25_index.search(query_text, top_k=2)
        keyword_docs = [item["text"] for item in bm25_results]
    except Exception as e:
        keyword_docs = []

    retrieved_docs = dense_docs + keyword_docs
    retrieved_docs = list(dict.fromkeys(retrieved_docs))[:5] # Deduplicate and limit to 5
    
    # 2. Augmentation Phase
    print("[4] Augmenting prompt with retrieved context...")
    final_prompt = build_rag_prompt(query_text, retrieved_docs)
    
    # 3. Generation Phase
    print("[5] Sending request to Groq LLM...")
    answer = generate_answer(final_prompt)
    
    print("\n=== FINAL ANSWER ===")
    print(answer)
    print("====================")
    
    return answer, retrieved_docs

if __name__ == "__main__":
    sample_question = "What are the fundamental rights regarding arrest?"
    # Since your work is on constitutional data, we filter by the Constitution.
    run_rag_pipeline(sample_question, filter_act="Constitution of Pakistan")
