"""
Ingestion script for Pakistani Case Law & Judicial Precedents (عدالتی نظائر).
Loads structured case law from data/caselaw_data.json and indexes into ChromaDB 'caselaw_collection'.
"""

import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "caselaw_data.json"
DB_PATH = PROJECT_ROOT / "data" / "chroma_db"
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def build_case_document_text(case: dict) -> str:
    """Construct rich textual representation of a case judgment for embedding."""
    statutes_str = ", ".join(case.get("statutes_cited", []))
    topics_str = ", ".join(case.get("legal_topics", []))
    
    text = (
        f"CITATION: {case.get('citation')}\n"
        f"CASE TITLE: {case.get('case_title')}\n"
        f"COURT: {case.get('court')} ({case.get('year')})\n"
        f"STATUTES CITED: {statutes_str}\n"
        f"LEGAL TOPICS: {topics_str}\n"
        f"RATIO DECIDENDI: {case.get('ratio_decidendi')}\n"
        f"FACTS SUMMARY: {case.get('facts_summary')}\n"
        f"DISPOSITION: {case.get('disposition')}\n"
        f"URDU RATIO: {case.get('urdu_ratio', '')}"
    )
    return text.strip()


def ingest_caselaw():
    """Load case law JSON and populate ChromaDB collection."""
    if not DATA_FILE.exists():
        print(f"[ERROR] Caselaw file not found at {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"Loaded {len(cases)} case precedents from {DATA_FILE.name}")
    print(f"Connecting to ChromaDB at {DB_PATH}...")
    
    from chromadb.config import Settings
    chroma_client = chromadb.PersistentClient(path=str(DB_PATH), settings=Settings(anonymized_telemetry=False))
    collection = chroma_client.get_or_create_collection(
        name="caselaw_collection",
        metadata={"description": "Pakistani Judicial Precedents (SCMR, PLD, PCrLJ, CLC)"}
    )

    print(f"Loading embedding model '{EMBED_MODEL_NAME}'...")
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    ids = []
    documents = []
    metadatas = []

    for case in cases:
        case_id = case.get("id") or case.get("citation", "").replace(" ", "_").lower()
        doc_text = build_case_document_text(case)
        
        statutes_str = "; ".join(case.get("statutes_cited", []))
        topics_str = "; ".join(case.get("legal_topics", []))
        
        metadata = {
            "citation": str(case.get("citation", "")),
            "case_title": str(case.get("case_title", "")),
            "court": str(case.get("court", "")),
            "year": int(case.get("year", 0)),
            "statutes_cited": statutes_str,
            "legal_topics": topics_str,
            "ratio_decidendi": str(case.get("ratio_decidendi", "")),
            "facts_summary": str(case.get("facts_summary", "")),
            "disposition": str(case.get("disposition", "")),
            "urdu_ratio": str(case.get("urdu_ratio", ""))
        }

        ids.append(case_id)
        documents.append(doc_text)
        metadatas.append(metadata)

    print(f"Generating embeddings for {len(documents)} case documents...")
    embeddings = embed_model.encode(documents, show_progress_bar=False, normalize_embeddings=True).tolist()

    print("Upserting into ChromaDB 'caselaw_collection'...")
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"[SUCCESS] Ingested {len(ids)} case precedents into 'caselaw_collection'!")
    print(f"Collection count: {collection.count()} items.")


if __name__ == "__main__":
    ingest_caselaw()
