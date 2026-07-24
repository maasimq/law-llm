import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rag_pipeline import answer_question

LOG_DIR = PROJECT_ROOT / "logs"
FINAL_CSV = LOG_DIR / "final_test_log_2.csv"
EDGE_CSV = LOG_DIR / "constitutional_edge_case_log.csv"
SUMMARY_TXT = LOG_DIR / "checkpoint9_quality_summary.txt"

IN_SCOPE_QUESTIONS = [
    "What does Article 8 of the Constitution say about laws inconsistent with fundamental rights?",
    "What protection does Article 9 provide for a person's life and liberty?",
    "What are the safeguards as to arrest and detention under Article 10?",
    "How does Article 10A describe the right to a fair trial?",
    "What does Article 11 prohibit regarding slavery and forced labour?",
    "How does Article 12 protect against retrospective punishment?",
    "What does Article 13 say about double jeopardy and self-incrimination?",
    "What rights does Article 14 guarantee for human dignity and privacy?",
    "What freedom does Article 15 give citizens in terms of movement?",
    "What assembly rights are protected by Article 16?",
    "How does Article 17 protect the right to form associations and unions?",
    "What business freedoms are granted by Article 18?",
    "What limits does Article 19 place on freedom of speech and expression?",
    "What does Article 19A guarantee regarding access to information?",
    "How does Article 20 protect freedom to practice religion?",
    "What does Article 21 say about taxation for religious purposes?",
    "What safeguards does Article 22 provide for education and religion?",
    "What does Article 23 guarantee about property ownership?",
    "How does Article 24 limit compulsory deprivation of property?",
    "What equality protections are provided under Article 25?",
    "What education right is described in Article 25A?",
    "How does Article 26 ensure equal access to public places?",
    "What non-discrimination protections are guaranteed by Article 27?",
    "How does Article 28 protect non-Muslim citizens?",
    "What is the constitutional status of fundamental rights under Article 8?",
    "Does Article 10 require informing an arrested person of the grounds for arrest?",
    "Does Article 19 permit reasonable restrictions on speech?",
    "What does Article 17 say about the right of public servants to join political parties?",
    "How does Article 11 treat child labour and forced labour?",
    "What compensation requirement is described in Article 24 when property is taken?",
]

EDGE_CASE_QUESTIONS = [
    "What is the corporate tax rate on rental income under Pakistani law?",
    "How do you register a trademark in Pakistan?",
    "What are the criminal penalties for theft under the PPC?",
    "Does the Pakistani Constitution regulate the price of gasoline?",
    "Can a non-resident obtain a Pakistani passport under the Constitution?",
    "What are the advertising restrictions under the Companies Act?",
    "Does the Constitution define the legal age for marriage?",
    "Which law governs the formation of a partnership firm in Pakistan?",
    "Is voter registration handled by the Constitution or by electoral law?",
    "Can the Constitution override a federal tax statute?",
]

CSV_FIELDS = [
    "id",
    "question",
    "category",
    "filter_act",
    "retrieved_chunks",
    "answer_length",
    "citation_present",
    "simple_language",
    "notes",
    "answer",
]


def review_answer(answer: str) -> dict:
    lower = (answer or "").lower()
    cite_keywords = ["article", "section", "constitution of pakistan", "act"]
    citation_present = any(k in lower for k in cite_keywords)
    words = answer.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    simple_language = avg_word_len < 7.5
    notes = []
    if not citation_present:
        notes.append("Missing citation")
    if "i do not have sufficient information" in lower:
        notes.append("Safe refusal or insufficient information")
    if not simple_language:
        notes.append("Language may be complex")
    return {
        "citation_present": citation_present,
        "simple_language": simple_language,
        "notes": "; ".join(notes) if notes else "Good",
    }


def run_batch(questions: list[str], category: str, output_path: Path, n_results: int = 4):
    rows = []
    for idx, question in enumerate(questions, start=1):
        print(f"Running {category} question {idx}/{len(questions)}")
        answer, retrieved = answer_question(question, filter_act="Constitution of Pakistan", n_results=n_results)
        review = review_answer(answer)
        rows.append({
            "id": idx,
            "question": question,
            "category": category,
            "filter_act": "Constitution of Pakistan",
            "retrieved_chunks": len(retrieved),
            "answer_length": len(answer or ""),
            "citation_present": review["citation_present"],
            "simple_language": review["simple_language"],
            "notes": review["notes"],
            "answer": answer.replace("\n", " "),
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_summary(in_scope_rows: list[dict], edge_rows: list[dict], path: Path):
    def score_row(row):
        score = 0
        score += 2 if row["citation_present"] else 0
        score += 1 if row["simple_language"] else 0
        score += 1 if "Safe refusal" in row["notes"] or "insufficient information" in row["notes"] else 0
        return score

    in_scope_scores = [score_row(row) for row in in_scope_rows]
    edge_scores = [score_row(row) for row in edge_rows]

    lines = [
        "Checkpoint 9 Constitution Quality Summary",
        "========================================",
        f"In-scope questions: {len(in_scope_rows)}",
        f"Edge-case questions: {len(edge_rows)}",
        "",
        "Summary:",
        "- All constitutional questions were run through the RAG pipeline with a Constitution filter.",
        "- The answer prompt requires exact Act/Article citation and a refusal when the information is not in-context.",
        "",
        f"In-scope citation coverage: {sum(1 for row in in_scope_rows if row['citation_present'])}/{len(in_scope_rows)}",
        f"In-scope simple-language coverage: {sum(1 for row in in_scope_rows if row['simple_language'])}/{len(in_scope_rows)}",
        f"Edge-case safe/refusal markers: {sum(1 for row in edge_rows if 'Safe refusal' in row['notes'])}/{len(edge_rows)}",
        "",
        "Notable findings and fixes applied:",
        "1. Increased dense retrieval depth to top 4 chunks for Constitution queries to improve article context coverage.",
        "2. Kept the Constitution filter active to avoid CPC/CrPC contamination and reinforce source specificity.",
        "3. Retained the explicit prompt instruction to refuse when context is insufficient, which is critical for safe edge-case behavior.",
        "",
        "Recommendations:",
        "- Review answers with missing citation flags and, if needed, augment the prompt further with a stricter citation-only response format.",
        "- Maintain the constitution filter when running future legal source-specific checkpoints.",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    in_scope_rows = run_batch(IN_SCOPE_QUESTIONS, "Constitution", FINAL_CSV, n_results=4)
    edge_rows = run_batch(EDGE_CASE_QUESTIONS, "EdgeCase", EDGE_CSV, n_results=4)
    write_summary(in_scope_rows, edge_rows, SUMMARY_TXT)
    print(f"\nFinished. Logs written to: {FINAL_CSV}, {EDGE_CSV}, {SUMMARY_TXT}")


if __name__ == "__main__":
    main()
