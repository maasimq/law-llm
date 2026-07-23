import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

from bm25_index import BM25KeywordIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = "llama-3.3-70b-versatile"


def load_prompt_template() -> str:
    """Load the prompt template used for the legal-answer generation step."""
    template_path = PROJECT_ROOT / "scripts" / "prompt_template.txt"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as handle:
            return handle.read()

    return """You are a Legal Assistant specializing in Pakistani Law.
INSTRUCTIONS:
1. Answer using only the provided context.
2. Cite the exact Act name and Section/Article number.
3. Explain complex terms simply.
CONTEXT:
{context}
USER QUESTION:
{question}
ANSWER:"""


def retrieve_context(query_text: str, collection, embed_model, top_k: int = 3, filter_act: str | None = None):
    """Retrieve the top matching dense vector chunks from ChromaDB."""
    query_embedding = embed_model.encode(query_text).tolist()
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
    }
    if filter_act:
        query_params["where"] = {"act_name": filter_act}

    results = collection.query(**query_params)
    return results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]


def retrieve_bm25_context(query_text: str, top_k: int = 2):
    """Retrieve additional keyword-based chunks using the BM25 index."""
    try:
        bm25_index = BM25KeywordIndex.from_chunk_index(
            PROJECT_ROOT / "data" / "chunks" / "chunk_index.csv",
            PROJECT_ROOT / "data" / "chunks",
        )
        results = bm25_index.search(query_text, top_k=top_k)
        return [item["text"] for item in results]
    except Exception:
        return []


def build_rag_prompt(query_text: str, retrieved_docs: list[str]) -> str:
    """Format the final prompt for the LLM using the loaded prompt template."""
    context_block = "\n\n---\n\n".join(retrieved_docs)
    template = load_prompt_template()
    return template.format(context=context_block, question=query_text)


def generate_answer(prompt: str) -> str:
    """Send the final prompt to the Groq model and return the answer."""
    completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=LLM_MODEL,
        temperature=0.1,
        max_tokens=1024,
    )
    return completion.choices[0].message.content


def answer_question(question: str, filter_act: str | None = None, n_results: int = 3) -> tuple[str, list[str]]:
    """Single question-to-answer function that combines retrieval and LLM generation."""
    db_path = PROJECT_ROOT / "data" / "chroma_db"
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_collection(name="law_collection")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    dense_docs, _ = retrieve_context(question, collection, embed_model, top_k=n_results, filter_act=filter_act)
    keyword_docs = retrieve_bm25_context(question, top_k=2)

    retrieved_docs = list(dict.fromkeys(dense_docs + keyword_docs))[:5]
    final_prompt = build_rag_prompt(question, retrieved_docs)
    answer = generate_answer(final_prompt)

    return answer, retrieved_docs


def run_rag_pipeline(query_text: str, filter_act: str | None = None):
    """Backward-compatible wrapper that keeps the existing test harness working."""
    print("\n=== RAG Pipeline Execution ===")
    print("[1] Retrieving legal context...")
    answer, retrieved_docs = answer_question(query_text, filter_act=filter_act)
    print("[2] Prompt built and answer generated.")
    print("\n=== FINAL ANSWER ===")
    print(answer)
    print("====================")
    return answer, retrieved_docs


if __name__ == "__main__":
    sample_question = "What are the fundamental rights regarding arrest?"
    run_rag_pipeline(sample_question, filter_act="Constitution of Pakistan")
