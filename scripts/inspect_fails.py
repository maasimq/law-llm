import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import answer_question

queries = [
    "hurt caused by rash or negligent driving",
    "criminal conspiracy"
]

for q in queries:
    print("=" * 60)
    print(f"QUERY: '{q}'")
    answer, docs = answer_question(q, n_results=5)
    print("RETRIEVED CHUNKS:")
    for i, d in enumerate(docs):
        lines = [line.strip() for line in d.split("\n") if line.strip()]
        header = " | ".join(lines[:3])
        print(f"  [{i+1}] {header[:120]}")
