# Law LLM — Pakistani Legal Assistant

A plain-English legal query application for laymen and lawyers, powered by Retrieval-Augmented Generation (RAG).

## Project Overview

This application answers questions about Pakistani law by searching a curated library of verified legal documents and generating clear, cited answers using a language model. It answers only from retrieved source text, cites the exact Section or Article, and states clearly when information is not available.

### Legal Sources Covered

| # | Legal Source | Coverage | Status |
|---|---|---|---|
| 1 | **Pakistan Penal Code, 1860 (PPC)** | Offences against human body, property, and public order | Planned |
| 2 | **Code of Criminal Procedure, 1898 (CrPC)** | Arrest, bail, FIR registration, and investigation | Planned |
| 3 | **Constitution of Pakistan, 1973** | Fundamental Rights — Articles 8 to 28 | In progress |

All content is sourced exclusively from [pakistancode.gov.pk](https://pakistancode.gov.pk) and [na.gov.pk](https://na.gov.pk).

---

## Current Progress

| Phase | Task | Status |
|---|---|---|
| Week 1 | Data collection & cleaning | Constitution complete |
| Week 1 | Chunking (~500 words, Section/Article aligned) | Constitution complete — 26 chunks |
| Week 2 | Embedding generation (`BAAI/bge-small-en-v1.5`, 384-dim) | Constitution complete — 26 embeddings |
| Week 2 | ChromaDB setup & retrieval testing | Next step |
| Week 3 | RAG pipeline & LLM integration | Pending |
| Week 4 | Streamlit UI & deployment | Pending |

**Checkpoint 5:** All 26 Constitution chunks embedded successfully. See `logs/checkpoint5_log.txt`.

---

## Technology Stack

| Component | Tool | Purpose |
|---|---|---|
| Language | Python 3.11 (64-bit) | Core development |
| LLM | Groq API — Llama 3.3 70B Versatile (free tier) | Answer generation |
| Embeddings | `BAAI/bge-small-en-v1.5` (384 dimensions) | Text vectorization |
| Vector DB | ChromaDB (local) | Chunk storage & retrieval |
| Keyword Search | BM25 | Fast lexical retrieval over chunk corpus |
| Orchestration | Plain Python (no LangChain/LlamaIndex) | Transparent pipeline |
| Frontend | Streamlit | Chat-style web UI |
| Deployment | Streamlit Community Cloud | Free public hosting |

---

## Repository Structure

```
law-llm/
├── data/
│   ├── raw/                  # Original source documents
│   │   ├── ppc/
│   │   ├── crpc/
│   │   └── constitution/
│   ├── clean/                # Cleaned text (one file per Section/Article)
│   │   └── data_index.csv
│   ├── chunks/               # Chunked text (~500 words each)
│   │   └── chunk_index.csv
│   └── embeddings/           # .npy vector files + embedding index
├── scripts/
│   ├── test_env.py           # Verify installed libraries
│   ├── test_groq.py          # Test Groq API connection
│   ├── download_sources.py   # Download legal source documents
│   ├── clean_data.py         # Clean and split raw documents
│   ├── process_constitution.py # Constitution-specific processing
│   ├── chunking.py           # Split cleaned text into chunks
│   ├── embed.py              # Generate embeddings for chunks
│   ├── npy.py                # Inspect .npy embedding files
│   ├── load_db.py            # Load embeddings into ChromaDB (upcoming)
│   ├── llm_call.py           # Groq API wrapper (upcoming)
│   └── rag_pipeline.py       # End-to-end RAG pipeline (upcoming)
├── logs/
│   └── checkpoint5_log.txt   # Embedding verification log
├── notebooks/
├── app/
│   └── app.py                # Streamlit application (upcoming)
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

> Use **64-bit Python 3.11**. The embedding model requires PyTorch, which does not support 32-bit Python.

### 3. Verify Setup

```bash
python scripts/test_env.py
python scripts/test_groq.py
```

Create a `.env` file in the project root with your Groq API key:

```
GROQ_API_KEY=your_key_here
```

Get a free key from [console.groq.com](https://console.groq.com/).

---

## Data Pipeline

Run these scripts from the **project root** in order:

```bash
# 1. Download source documents
python scripts/download_sources.py

# 2. Clean and split into Section/Article files
python scripts/clean_data.py

# 3. Split cleaned text into ~500-word chunks
python scripts/chunking.py

# 4. Generate embeddings (test first, then full run)
python scripts/embed.py --test
python scripts/embed.py
```

### Inspect Embeddings

```bash
python scripts/npy.py
```

This prints the shape and sample values of an embedding file. Each vector has **384 dimensions**.

---

## Constitution Dataset (Completed)

| Item | Count |
|---|---|
| Cleaned Articles (Articles 8–28) | 24 files |
| Text chunks | 26 |
| Embeddings (`.npy`) | 26 |
| Embedding dimension | 384 |

Index files:
- `data/clean/data_index.csv` — cleaned document inventory
- `data/chunks/chunk_index.csv` — chunk metadata
- `data/embeddings/embedding_index.json` — embedding metadata

---

## Development Schedule

| Week | Phase | Focus |
|---|---|---|
| **Week 1** | Data Engineering | Collection, cleaning, chunking |
| **Week 2** | Knowledge Base | Embeddings, ChromaDB, retrieval testing |
| **Week 3** | RAG Pipeline | LLM integration, prompt engineering, testing |
| **Week 4** | Deployment | Streamlit UI, cloud deployment, user testing |

---

## Working Standards

- All code committed daily with descriptive messages
- No hardcoded API keys — use `.env` only
- All scripts must run from a clean `requirements.txt` install
- The app must **never fabricate** a Section, Article, or citation
- If retrieval finds no match, the app says so honestly

---

## Team

- **Supervisor:** Dr. Aasim Qureshi, FAST-NUCES Lahore
- Muhammad Abdul Raheem Khan — Team Lead
- Ahmad Rasheed
- Muhammad Aliyan Mumtaz

## License

This project is for academic/research purposes under FAST-NUCES Lahore.
