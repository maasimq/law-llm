# ⚖️ Law LLM — Pakistani Legal Assistant

A plain-English legal query application for laymen and lawyers, powered by Retrieval-Augmented Generation (RAG).

## Project Overview

This application answers questions about Pakistani law by searching a curated library of verified legal documents and generating clear, cited answers using a language model. It answers only from retrieved source text, cites the exact Section or Article, and states clearly when information is not available.

### Legal Sources Covered

| # | Legal Source | Coverage | Status |
|---|---|---|---|
| 1 | **Pakistan Penal Code, 1860 (PPC)** | Offences against human body, property, and public order | Data & Embeddings Processed |
| 2 | **Code of Criminal Procedure, 1898 (CrPC)** | Arrest, bail, FIR registration, and investigation | Data & Embeddings Processed |
| 3 | **Constitution of Pakistan, 1973** | Fundamental Rights — Articles 8 to 28 | Complete |

All content is sourced exclusively from [pakistancode.gov.pk](https://pakistancode.gov.pk) and [na.gov.pk](https://na.gov.pk).

---

## Current Progress

| Phase | Task | Status |
|---|---|---|
| Week 1 | Data collection & cleaning (PPC, CrPC, Constitution) | Complete |
| Week 1 | Chunking (~500 words, Section/Article aligned) | Complete |
| Week 2 | Embedding generation (`BAAI/bge-small-en-v1.5`, 384-dim) | Complete |
| Week 2 | ChromaDB setup & hybrid retrieval (Dense + BM25) | Complete |
| Week 3 | RAG pipeline orchestration & prompt engineering | Complete |
| Week 3 | LLM Integration & Prompt Validation (Groq / Llama-3.3 70B) | Complete |
| Week 4 | Streamlit UI & cloud deployment | Upcoming |

---

## Technology Stack

| Component | Tool | Purpose |
|---|---|---|
| Language | Python 3.11 (64-bit) | Core development |
| LLM | Groq API — Llama 3.3 70B Versatile | Answer generation |
| Embeddings | `BAAI/bge-small-en-v1.5` (384 dimensions) | Text vectorization |
| Vector DB | ChromaDB (local, persistent) | Chunk storage & similarity retrieval |
| Keyword Search | BM25 | Fast lexical retrieval over chunk corpus |
| Orchestration | Plain Python (no LangChain/LlamaIndex) | Transparent pipeline |
| Frontend | Streamlit | Chat-style web UI |
| Deployment | Streamlit Community Cloud | Free public hosting |

---

## Repository Structure

```
law-llm/
├── data/
│   ├── raw/                  # Original legal source documents
│   │   ├── ppc/
│   │   ├── crpc/
│   │   └── constitution/
│   ├── clean/                # Cleaned text (one file per Section/Article)
│   ├── chunks/               # Chunked text (~500 words each) + chunk_index.csv
│   ├── embeddings/           # .npy vector files + embedding index
│   └── chroma_db/            # Persistent ChromaDB vector store
├── scripts/
│   ├── test_env.py                  # Verify installed libraries
│   ├── test_groq.py                 # Test Groq API connection
│   ├── download_sources.py          # Download legal source documents
│   ├── clean_data.py                # Clean and split raw documents
│   ├── process_constitution.py      # Constitution-specific processing
│   ├── process_crpc.py              # CrPC-specific processing
│   ├── setup_chromadb.py            # Initialize and populate ChromaDB
│   ├── bm25_index.py                # BM25 keyword search index
│   ├── query_chromadb.py            # Test ChromaDB similarity search
│   ├── validate_retriever.py        # 10 test queries across PPC/CrPC/Constitution
│   ├── llm_call.py                  # Groq API LLM call wrapper
│   ├── test_llm_baseline.py         # Test raw LLM generation without retrieval
│   ├── validate_prompt_template.py  # Validate answers against prompt rules
│   └── rag_pipeline.py              # End-to-end RAG pipeline
├── logs/                            # Output logs and validation results
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/abdul-raheem-fast/law-llm.git
cd law-llm
```

### 2. Set Up the Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

> Use **64-bit Python 3.11**.

### 3. Configure API Key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

Get a free key from [console.groq.com](https://console.groq.com/).

### 4. Run RAG Pipeline & Validation

```bash
# Run the full RAG pipeline (Retrieval + Prompt Formatting + LLM Generation)
python scripts/rag_pipeline.py

# Test baseline LLM performance (without retrieval)
python scripts/test_llm_baseline.py

# Validate prompt template rules and citations
python scripts/validate_prompt_template.py

# Run 10 multi-source retriever validation queries
python scripts/validate_retriever.py
```

---

## Working Standards

- All code committed daily with clear descriptive messages (no day numbers in commit logs)
- No hardcoded API keys — use `.env` only
- All scripts must run cleanly from `requirements.txt`
- The application must **never fabricate** a Section, Article, or citation
- If retrieval finds no match, the app states so honestly

---

## Team

- **Supervisor:** Dr. Aasim Qureshi, FAST-NUCES Lahore
- **Muhammad Abdul Raheem Khan** — Team Lead
- **Ahmad Rasheed**
- **Muhammad Aliyan Mumtaz**

---

## License

This project is for academic/research purposes under FAST-NUCES Lahore.
