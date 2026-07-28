import json
import os
import re
import sys
from datetime import datetime
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
LOG_DIR = PROJECT_ROOT / "logs"

load_dotenv()
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
LLM_MODEL = "llama-3.3-70b-versatile"
REFUSAL_SENTENCE = "I do not have sufficient information in the provided legal text to answer this question."


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


def retrieve_context(query_text: str, collection, embed_model, top_k: int = 3, filter_act: str | None = None, max_distance: float = 0.65):
    """Retrieve the top matching dense vector chunks from ChromaDB, filtered by similarity distance."""
    prefixed_query = "Represent this sentence for searching relevant passages: " + query_text
    query_embedding = embed_model.encode(prefixed_query, normalize_embeddings=True).tolist()
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"]
    }
    if filter_act:
        query_params["where"] = {"act_name": filter_act}

    results = collection.query(**query_params)
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    filtered_docs = []
    filtered_metas = []
    for doc, dist, meta in zip(docs, distances, metadatas):
        # Cosine distance: lower is more similar (0 = identical, 1 = orthogonal)
        if dist <= max_distance:
            filtered_docs.append(doc)
            filtered_metas.append(meta)

    return filtered_docs, filtered_metas


def retrieve_bm25_context(query_text: str, filter_act: str | None = None, top_k: int = 2):
    """Retrieve additional keyword-based chunks using the BM25 index with Act filtering."""
    try:
        bm25_index = BM25KeywordIndex.from_chunk_index(
            PROJECT_ROOT / "data" / "chunks" / "chunk_index.csv",
            PROJECT_ROOT / "data" / "chunks",
        )
        # Search a larger set if we need to filter by Act
        results = bm25_index.search(query_text, top_k=top_k * 4 if filter_act else top_k)
        
        filtered_texts = []
        for item in results:
            text = item.get("text", "")
            if filter_act:
                act_lower = filter_act.lower()
                text_lower = text.lower()
                if "constitution" in act_lower and ("constitution" not in text_lower and not text_lower.startswith("10 ") and not text_lower.startswith("25 ") and "article" not in text_lower):
                    continue
                elif "penal code" in act_lower and ("penal code" not in text_lower and "ppc" not in text_lower):
                    continue
                elif "criminal procedure" in act_lower and ("criminal procedure" not in text_lower and "crpc" not in text_lower):
                    continue
            filtered_texts.append(text)
            if len(filtered_texts) >= top_k:
                break

        return filtered_texts
    except Exception:
        return []


def build_rag_prompt(query_text: str, retrieved_docs: list[str]) -> str:
    """Format the final prompt for the LLM using the loaded prompt template."""
    # Truncate each document to ~3000 characters (approx 750 tokens)
    # With 3 chunks max, total context stays under ~2250 tokens + prompt,
    # well within Groq free-tier 12,000 TPM limit.
    truncated_docs = [doc[:3000] for doc in retrieved_docs]
    context_block = "\n\n---\n\n".join(truncated_docs)
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


def is_out_of_scope_question(question: str, filter_act: str | None = None) -> bool:
    """Return True when a constitution-specific pipeline is asked a non-constitutional question."""
    if filter_act != "Constitution of Pakistan":
        return False

    normalized = " ".join((question or "").lower().split())

    constitutional_terms = [
        "article",
        "constitution",
        "fundamental rights",
        "fundamental right",
        "right to",
        "rights",
        "liberty",
        "arrest",
        "detention",
        "slavery",
        "forced labour",
        "forced labor",
        "fair trial",
        "property",
        "education",
        "religion",
        "speech",
        "expression",
        "association",
        "union",
        "assembly",
        "movement",
        "privacy",
        "dignity",
        "equality",
        "public places",
        "discrimination",
        "compulsory deprivation",
        "religious purposes",
        "citizen",
        "double jeopardy",
        "self-incrimination",
        "tried twice",
    ]

    out_of_scope_terms = [
        "tax rate",
        "tax",
        "rental income",
        "trademark",
        "register",
        "registration",
        "criminal penalty",
        "criminal penalties",
        "theft",
        "ppc",
        "companies act",
        "passport",
        "advertising",
        "marriage",
        "partnership",
        "voter registration",
        "gasoline",
        "company",
        "corporate",
        "business",
        "licence",
        "license",
        "bail",
        "fir",
        "contract",
        "statute",
        "law governs",
        "income",
        "revenue",
    ]

    if any(term in normalized for term in constitutional_terms):
        return False

    return any(term in normalized for term in out_of_scope_terms)


import csv

def detect_act_from_query(query: str) -> str | None:
    """Infer target Act from user query string if not explicitly passed."""
    q_lower = query.lower()
    if "crpc" in q_lower or "criminal procedure" in q_lower:
        return "Code of Criminal Procedure, 1898"
    elif "ppc" in q_lower or "penal code" in q_lower:
        return "Pakistan Penal Code, 1860"
    elif "constitution" in q_lower or "article" in q_lower:
        return "Constitution of Pakistan"
    return None


def extract_requested_statute(query_text: str) -> tuple[str | None, str | None]:
    """
    Detect explicit section/article queries e.g.
    'Article 10A', 'Article 10', 'Section 497', 'Section 302 PPC', '497 CrPC'.
    Returns (act_name, section_article_number).
    """
    q_lower = query_text.lower()
    act = detect_act_from_query(query_text)
    
    # Check for Article XX or Article XXA
    art_match = re.search(r'article\s*(\d+[a-z]?)', q_lower)
    if art_match:
        sec = art_match.group(1).upper()
        return "Constitution of Pakistan", sec

    # Check for Section XXX or Section XXXA
    sec_match = re.search(r'section\s*(\d+[a-z]?)', q_lower)
    if sec_match:
        sec = sec_match.group(1).upper()
        return act, sec

    # Check for number + Act e.g. "497 crpc" or "302 ppc"
    num_act_match = re.search(r'(\d+[a-z]?)\s*(crpc|ppc)', q_lower)
    if num_act_match:
        sec = num_act_match.group(1).upper()
        act_key = num_act_match.group(2)
        target_act = "Code of Criminal Procedure, 1898" if act_key == "crpc" else "Pakistan Penal Code, 1860"
        return target_act, sec

    return act, None


def get_exact_chunk_by_statute(target_act: str, target_sec: str) -> str | None:
    """Look up exact chunk text for given Act and Section/Article."""
    try:
        chunks_dir = PROJECT_ROOT / "data" / "chunks"
        sec_clean = target_sec.lower().strip()
        
        # 1. Direct filename check for Constitution & PPC
        if "constitution" in target_act.lower():
            fname = f"constitution_article_{sec_clean}_chunk_0.txt"
            fpath = chunks_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as handle:
                    return handle.read()

        elif "penal code" in target_act.lower() or "ppc" in target_act.lower():
            fname = f"ppc_section_{sec_clean}_chunk_0.txt"
            fpath = chunks_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as handle:
                    return handle.read()

        # 2. CSV index lookup
        csv_path = chunks_dir / "chunk_index.csv"
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    act = row.get("act_name", "").strip()
                    sec = row.get("section_article_number", "").strip().upper()
                    if act.lower() == target_act.lower() and sec == target_sec.upper():
                        chunk_file = chunks_dir / row["chunk_filename"]
                        if chunk_file.exists():
                            with open(chunk_file, "r", encoding="utf-8") as handle:
                                return handle.read()

        # 3. Header text scanning fallback
        for file in chunks_dir.glob("*.txt"):
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                header = [f.readline() for _ in range(6)]
                header_text = "".join(header).upper()
                target_str = f"SECTION: {target_sec.upper()}"
                target_str2 = f"SECTION/ARTICLE: {target_sec.upper()}"
                if target_str in header_text or target_str2 in header_text:
                    f.seek(0)
                    return f.read()

    except Exception as e:
        print(f"[EXACT MATCH LOOKUP ERROR] {e}", file=sys.stderr)
        
    return None


def answer_question(question: str, filter_act: str | None = None, n_results: int = 3) -> tuple[str, list[str]]:
    """Single question-to-answer function that combines retrieval and LLM generation."""
    target_act, target_sec = extract_requested_statute(question)
    exact_match_chunk = None
    
    if target_act and target_sec:
        exact_match_chunk = get_exact_chunk_by_statute(target_act, target_sec)

    filter_act = target_act or filter_act or detect_act_from_query(question)

    if is_out_of_scope_question(question, filter_act=filter_act):
        return REFUSAL_SENTENCE, []

    db_path = PROJECT_ROOT / "data" / "chroma_db"
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_collection(name="law_collection")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    if filter_act == "Constitution of Pakistan" and n_results < 4:
        n_results = 4

    dense_docs, _ = retrieve_context(question, collection, embed_model, top_k=n_results, filter_act=filter_act)
    keyword_top_k = 2 if filter_act == "Constitution of Pakistan" else 1
    keyword_docs = retrieve_bm25_context(question, filter_act=filter_act, top_k=keyword_top_k)

    all_docs = []
    if exact_match_chunk:
        all_docs.append(exact_match_chunk)

    for doc in dense_docs + keyword_docs:
        if doc not in all_docs:
            all_docs.append(doc)

    # If an exact match was found (e.g. Article 10A or Section 497), restrict to relevant target Act chunks
    if exact_match_chunk and target_act:
        filtered_all = [exact_match_chunk]
        if target_sec:
            sec_num = target_sec.upper()
            for d in all_docs[1:]:
                d_upper = d.upper()
                # Only keep secondary chunk if it matches the target act and specifically mentions the section/topic
                if target_act.lower() in d.lower() and (f"SECTION: {sec_num}" in d_upper or f"ARTICLE: {sec_num}" in d_upper or ("BAIL" in d_upper if sec_num == "497" else False)):
                    filtered_all.append(d)
        else:
            for d in all_docs[1:]:
                if target_act.lower() in d.lower():
                    filtered_all.append(d)
        all_docs = filtered_all

    # Cap at 3 chunks total to stay under Groq free-tier TPM limits
    retrieved_docs = all_docs[:3]

    # Guardrail: Check if a specific Act was requested but no matching chunks were retrieved
    if filter_act and not retrieved_docs:
        guardrail_msg = (
            f"I couldn't find an exact match for that query in the {filter_act}. "
            "Please verify the section number and Act name (e.g. Section 497 CrPC for Bail vs. Section 497 PPC for Adultery)."
        )
        return guardrail_msg, []

    final_prompt = build_rag_prompt(question, retrieved_docs)
    answer = generate_answer(final_prompt)

    # If the answer is a refusal / out-of-scope response, return empty sources so no irrelevant citation cards render
    answer_lower = answer.lower()
    refusal_keywords = [
        "do not have sufficient information",
        "does not mention",
        "does not provide",
        "not mentioned",
        "no relevant information",
        "not explicitly stated",
        "not contained in the provided",
        "not provided in the given context",
    ]
    if REFUSAL_SENTENCE in answer or any(kw in answer_lower for kw in refusal_keywords):
        return answer, []

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


def run_logging_pipeline(questions: list[str], log_file: str | None = None, filter_act: str | None = None):
    """Run the pipeline over multiple questions and persist a structured JSON log."""
    LOG_DIR.mkdir(exist_ok=True)

    output_path = Path(log_file) if log_file else LOG_DIR / "pipeline_run_log.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for index, question in enumerate(questions, start=1):
        answer, retrieved_docs = answer_question(question, filter_act=filter_act)
        results.append(
            {
                "question_id": index,
                "question": question,
                "filter_act": filter_act,
                "answer": answer,
                "retrieved_chunk_count": len(retrieved_docs),
                "retrieved_chunks": retrieved_docs,
            }
        )

    payload = {
        "timestamp": datetime.now().isoformat(),
        "model": LLM_MODEL,
        "total_questions": len(questions),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    return payload


if __name__ == "__main__":
    sample_questions = [
        "What are the safeguards as to arrest and detention under Article 10?",
        "Does the Constitution prohibit forced labour and slavery?",
    ]
    run_logging_pipeline(sample_questions, filter_act="Constitution of Pakistan")
