import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import answer_question, resolve_alias_chunks

q = "My client has been arrested and charged under PPC Section 379 (Theft) and PPC Section 420 (Cheating), and has been in police custody for 14 days without a formal charge sheet. As his defense counsel, what are the statutory grounds under CrPC Section 497 to apply for his post-arrest bail in court?"

print("=== ALIAS DOCS FOUND ===")
alias_docs = resolve_alias_chunks(q)
for d in alias_docs:
    lines = [line.strip() for line in d.split("\n") if line.strip()]
    print("  ->", lines[:2])

print("\n=== ALL RETRIEVED DOCS ===")
ans, docs = answer_question(q, mode="advocate")
for i, d in enumerate(docs):
    lines = [line.strip() for line in d.split("\n") if line.strip()]
    print(f"  Doc {i+1}:", lines[:2])
