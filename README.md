# ⚖️ Law LLM — Pakistani Legal Assistant

> **A state-of-the-art, plain-English legal query application powered by Retrieval-Augmented Generation (RAG), designed to bridge the gap between complex legal jargon and accessible knowledge for laymen and lawyers alike.**

## 📖 Project Overview

Navigating statutory law can be daunting. **Law LLM** solves this by searching a highly-curated, verified library of Pakistani legal documents and generating clear, accurate, and easy-to-understand answers using advanced language models. 

Built with strict AI guardrails, the application **only** answers based on retrieved source text, always cites the exact Section or Article, and refuses to hallucinate when information is out of scope.

### 🏛️ Legal Sources Covered

| Legal Source | Coverage Scope |
|---|---|
| **Pakistan Penal Code, 1860 (PPC)** | Offences against human body, property, and public order |
| **Code of Criminal Procedure, 1898 (CrPC)** | Arrest, bail, FIR registration, and investigation |
| **Constitution of Pakistan, 1973** | Fundamental Rights (Articles 8 to 28) |

*All content is sourced exclusively from official government portals: [pakistancode.gov.pk](https://pakistancode.gov.pk) and [na.gov.pk](https://na.gov.pk).*

---

## ✨ Key Features & Architecture

We built a robust, multi-stage retrieval pipeline to ensure maximum accuracy and resolve complex cross-Act ambiguities (e.g., distinguishing between *PPC § 497* for Adultery and *CrPC § 497* for Bail).

1. **Intelligent Exact-Match Routing:** Instantly routes common, single-word queries (e.g., "FIR", "theft") directly to their authoritative sections.

2. **Hybrid Retrieval:** Combines the semantic understanding of dense vector embeddings (`bge-small`) with the exact keyword precision of sparse retrieval (`BM25`) using min-max normalized score fusion.

3. **Cross-Encoder Re-Ranking:** Passes the top hybrid candidates through a powerful cross-encoder (`ms-marco-MiniLM-L-6-v2`) for pinpoint sorting, ensuring the most relevant legal chunk is always fed to the LLM.

4. **Dynamic Latency Optimization:** Automatically bypasses the heavy cross-encoder step when a query has a dominant, clear-cut match, saving massive compute time without sacrificing accuracy.

5. **Interactive UI:** A beautiful, responsive chat interface built in Streamlit featuring expandable citation panels to view the raw statutory source text.

---

## 🛠️ Technology Stack

| Component | Technology Used |
|---|---|
| **Language** | Python 3.11 |
| **LLM Engine** | Groq API — Llama 3.3 70B Versatile |
| **Embeddings** | `BAAI/bge-small-en-v1.5` (384-dimensional dense vectors) |
| **Re-Ranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Vector Database** | ChromaDB (local, persistent storage) |
| **Keyword Index** | BM25 (Sparse retrieval) |
| **Frontend** | Streamlit |

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/maasimq/law-llm.git
cd law-llm
```

### 2. Set Up the Environment
*Note: Use 64-bit Python 3.11.*
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the root directory and add your free [Groq API key](https://console.groq.com/):
```env
GROQ_API_KEY=your_key_here
```

### 4. Run the Application
Launch the interactive Streamlit chat interface:
```bash
streamlit run app/app.py
```

### 5. Run the Automated Evaluation Harness
To test the pipeline's retrieval accuracy across aliased and non-aliased legal queries:
```bash
python scripts/retrieval_eval.py
```

---

## 🏗️ Repository Structure

```text
law-llm/
├── app/
│   └── app.py                       # Main Streamlit chat interface
├── data/
│   ├── raw/                         # Original PDF/TXT legal documents
│   ├── clean/                       # Cleaned text (split by Section/Article)
│   ├── chunks/                      # ~500-word logical chunks
│   └── chroma_db/                   # Persistent vector database
├── scripts/
│   ├── rag_pipeline.py              # Core Hybrid + Re-ranking RAG engine
│   ├── retrieval_eval.py            # Evaluation harness for retrieval metrics
│   ├── setup_chromadb.py            # Vector DB initialization
│   ├── bm25_index.py                # Sparse keyword indexing
│   └── ...                          # Data cleaning & utility scripts
├── .env                             # (Ignored) Environment variables
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## 👥 Team & Acknowledgments

This project was developed as an academic and research initiative under FAST-NUCES Lahore.

- **Supervisor:** Dr. Aasim Qureshi
- **Team Lead:** Muhammad Abdul Raheem Khan
- **Developers:** Ahmad Rasheed, Muhammad Aliyan Mumtaz

---
*Disclaimer: Law LLM provides informational statutory references only. It does not constitute formal legal advice.*
