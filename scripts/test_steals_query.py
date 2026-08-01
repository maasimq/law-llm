import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rag_pipeline import answer_question

def main():
    query = "What happens if someone steals my phone?"
    print(f"Testing Query: '{query}'")
    answer, sources = answer_question(query)
    print("\n=== ANSWER ===")
    print(answer)
    print("\n=== RETRIEVED SOURCES ===")
    for i, s in enumerate(sources):
        lines = s.split("\n")
        print(f"Source {i+1}: {lines[0]} | {lines[1]}")

if __name__ == "__main__":
    main()
