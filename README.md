![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

# <img src="app/favicon.png" width="32" height="32" valign="middle"> Law LLM — Pakistani Legal Assistant

> A RAG-powered legal assistant that searches Pakistani statutory law and answers questions in plain English — or Urdu — with exact section citations.

---

![Landing screen](docs/screenshot-landing.png)
![Cited answer example](docs/screenshot-answer.png)

---

## What It Does

Ask a question. Get a cited, grounded answer from the actual text of Pakistani law.

```
"What happens if someone steals my phone?"
→ PPC § 378 (Theft), § 379 (Punishment for Theft)

"ضمانت کیسے ملتی ہے؟"
→ CrPC § 497, § 498 — full answer in Urdu script

"Draft an FIR for cheating"
→ Formal FIR draft with placeholders, cited under PPC § 420
```

Every answer is grounded in retrieved statutory text — no hallucination, no invented sections. The hybrid retrieval + cross-encoder re-ranking pipeline achieves **100% pass rate (31/31)** on the labeled evaluation set, up from a 74.2% baseline before the pipeline was introduced.

---

## Legal Sources

| Act | Coverage |
|---|---|
| **Pakistan Penal Code, 1860** | Offences — body, property, public order |
| **Code of Criminal Procedure, 1898** | Arrest, bail, FIR, investigation |
| **Constitution of Pakistan, 1973** | Fundamental Rights — Articles 8 to 28 |

*Sourced exclusively from [pakistancode.gov.pk](https://pakistancode.gov.pk) and [na.gov.pk](https://na.gov.pk).*

> **Scope & Completeness Note**: Knowledge base completeness is verified against a curated core inventory of major offences, criminal procedures, and Fundamental Rights. A full section-by-section reconciliation against the complete statutory text was not performed.

---

## Key Features

### 🗣️ / ⚖️ Two Modes

| | Layman | Advocate |
|---|---|---|
| **Audience** | General public | Legal practitioners |
| **Output** | Plain-English explanations | Section-by-section legal analysis |
| **Documents** | ❌ Blocked with redirect | ✅ FIR drafts, legal notices, case briefs |
| **Mode lock** | Locks on first message | Locks on first message |

---

### 🔍 Multi-Stage Retrieval Pipeline

```
Query
  │
  ├─ 1. Alias Routing      "theft" → PPC § 378/379 (direct lookup, no search)
  ├─ 2. Exact Section      "Section 302 PPC" → fetched by filename/CSV index
  ├─ 3. Hybrid Search      Dense (BGE embeddings) + Sparse (BM25) → score fusion
  └─ 4. Cross-Encoder      ms-marco-MiniLM re-ranks top candidates → top 3 chunks
```

Resolves cross-Act ambiguities automatically — e.g. *PPC § 497* (Adultery) vs *CrPC § 497* (Bail) are never confused.

---

### 📜 Judicial Precedents & Case Law (عدالتی نظائر)

- Dual-retriever pipeline indexing **100 landmark Supreme Court and High Court judgments** (`SCMR`, `PLD`, `PCrLJ`, `CLC`)
- Comprehensive coverage across Bail (§ 497/498 CrPC), Murder (§ 302 PPC), FIR Law (§ 154 CrPC), Religious Offences (§ 295-C PPC), Cheque Dishonor (§ 489-F PPC), and Fundamental Rights (Arts. 9, 10A, 14, 199)
- Automatic extraction and presentation of *Ratio Decidendi* (core legal principle) alongside statutory sections
- Interactive case law precedent cards with full case summary, applicable statutes, and bilingual Urdu ratio summaries

---

### 🌐 Urdu & Roman Urdu Support

- Queries in Urdu or Roman Urdu are translated to English before retrieval (via `openai/gpt-oss-20b`)
- Responses are generated back in native Urdu script (نستعلیق) with correct legal headings
- Islamic legal terms rendered in native script, including Qisas and Diyat terminology used in the Pakistan Penal Code (قتلِ عمد، قصاص، دیت، تعزیر)

---

### 💬 Chat Interface

- Persistent multi-session history with auto-generated 2–3 word titles
- Stage-by-stage loading indicators: *Translating query... → Analyzing laws... → Drafting answer...*
- Expandable citation cards showing the raw statutory source text
- Signature judicial precedent cards for court-ready advocate case briefs
- Dark mode with gold accent design system

---

## Known Limitations

- **Scope:** Coverage is limited to the PPC, CrPC, Constitution Fundamental Rights (Arts. 8–28), and curated Supreme Court/High Court reported judgments. Other specialized branches (tax, corporate, family) will return an out-of-scope notice.
- **Drafted documents:** FIRs and case briefs generated in Advocate mode are structured templates with placeholders. They are not filed-ready legal documents and must be reviewed by a licensed advocate before use.
- **Urdu retrieval:** Urdu and Roman Urdu queries are translated to English before retrieval. Translation quality can affect retrieval accuracy — unusual phrasing or dialect may reduce precision.

---

## Technology Stack

| Component | Technology |
|---|---|
| **LLM (Primary)** | Groq — `openai/gpt-oss-120b` |
| **Translation, Verification & Titles** | Groq — `openai/gpt-oss-20b` (Fallback: `qwen/qwen3.6-27b`) |
| **Embeddings** | `BAAI/bge-small-en-v1.5` (384-dim) |
| **Re-Ranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Vector DB** | ChromaDB (`law_collection` + `caselaw_collection`) |
| **Keyword Index** | BM25 (Rank-BM25) |
| **Frontend** | Streamlit + Custom CSS |
| **Language** | Python 3.11 |

---

## Quick Start

**1. Clone**
```bash
git clone https://github.com/maasimq/law-llm.git
cd law-llm
```

**2. Install**
```bash
python -m venv .venv
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

**3. Add API key** — create `.env`:
```env
GROQ_API_KEY=your_key_here
```

**4. Run**
```bash
streamlit run app/app.py
```

**5. Evaluate retrieval** *(optional)*
```bash
python scripts/retrieval_eval.py
```
Current pipeline scores **100% (31/31)** on the labeled evaluation set.

---

## Repository Structure

```
law-llm/
├── app/
│   ├── app.py                        # Streamlit chat interface
│   └── styles.css                    # Custom CSS design system
├── data/
│   ├── raw/                          # Source PDFs / TXT
│   ├── clean/                        # Cleaned, section-split text
│   ├── chunks/                       # Indexed ~500-word chunks
│   └── chroma_db/                    # Persistent vector store
├── docs/
│   ├── screenshot-landing.png        # Landing page screenshot
│   └── screenshot-answer.png        # Cited answer screenshot
├── scripts/
│   ├── rag_pipeline.py               # Core RAG engine
│   ├── prompt_template.txt           # Layman mode prompt
│   ├── advocate_prompt_template.txt  # Advocate mode prompt
│   ├── bm25_index.py                 # BM25 keyword index
│   ├── setup_chromadb.py             # Vector DB setup
│   └── retrieval_eval.py             # Evaluation harness
├── .env                              # API keys (git-ignored)
├── LICENSE
└── requirements.txt
```

---

## Team

Developed as an academic research project at **FAST-NUCES Lahore**.

| Role | Name |
|---|---|
| Supervisor | Dr. Aasim Qureshi |
| Team Lead | Muhammad Abdul Raheem Khan |
| Developer | Ahmad Rasheed |
| Developer | Muhammad Aliyan Mumtaz |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Law LLM provides statutory reference information only. It does not constitute formal legal advice.*
