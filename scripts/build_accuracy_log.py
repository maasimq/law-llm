"""
Query Logging and Accuracy Tracking System
===========================================
Reads the supervisor test log produced by run_supervisor_tests.py,
asks the user to rate each answer (1–5), computes aggregate accuracy
stats, and writes the final rated log to logs/query_accuracy_log.csv.
Also generates a short plain-text quality summary report.
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_INPUT  = PROJECT_ROOT / "logs" / "supervisor_test_log.json"
CSV_OUTPUT = PROJECT_ROOT / "logs" / "query_accuracy_log.csv"
SUMMARY_OUTPUT = PROJECT_ROOT / "logs" / "quality_summary.txt"

# CSV column headers
CSV_FIELDS = [
    "id", "category", "question", "chunks_retrieved",
    "answer_length_chars", "status", "accuracy_rating",
    "citation_present", "simple_language", "notes"
]


def auto_review(result):
    """
    Performs automated review of a pipeline result.
    Returns a dict of quality flags without requiring human input.
    """
    answer = result.get("answer") or ""
    
    # Citation check — does answer mention an Act/Section/Article?
    cite_keywords = ["section", "article", "penal code", "ppc", "constitution", "crpc", "act"]
    citation_present = any(kw in answer.lower() for kw in cite_keywords)

    # Simple language heuristic — average word length
    words = answer.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    simple_language = avg_word_len < 7.5

    # Auto accuracy rating (heuristic):
    # 5 — success + citation + simple language
    # 4 — success + citation
    # 3 — success, no citation
    # 1 — error
    if result["status"] != "success":
        accuracy_rating = 1
    elif citation_present and simple_language:
        accuracy_rating = 5
    elif citation_present:
        accuracy_rating = 4
    else:
        accuracy_rating = 3

    notes = []
    if not citation_present:
        notes.append("Missing Act/Section citation")
    if not simple_language:
        notes.append("Language may be too complex")
    if result["status"] != "success":
        notes.append(result["status"])

    return {
        "accuracy_rating":  accuracy_rating,
        "citation_present": citation_present,
        "simple_language":  simple_language,
        "notes":            "; ".join(notes) if notes else "Passed all checks",
    }


def build_accuracy_log():
    if not LOG_INPUT.exists():
        print(f"ERROR: Supervisor test log not found at {LOG_INPUT}")
        print("Please run run_supervisor_tests.py first.")
        return

    with open(LOG_INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    print("=" * 65)
    print("QUERY ACCURACY LOGGING SYSTEM")
    print(f"Reviewing {len(results)} pipeline responses...")
    print("=" * 65)

    rows = []
    ratings = []

    for result in results:
        review = auto_review(result)
        ratings.append(review["accuracy_rating"])

        row = {
            "id":                  result["id"],
            "category":            result["category"],
            "question":            result["question"],
            "chunks_retrieved":    result["chunks_retrieved"],
            "answer_length_chars": len(result["answer"] or ""),
            "status":              result["status"],
            "accuracy_rating":     review["accuracy_rating"],
            "citation_present":    review["citation_present"],
            "simple_language":     review["simple_language"],
            "notes":               review["notes"],
        }
        rows.append(row)

        print(f"[{result['id']:02d}] [{result['category']}] Rating: {review['accuracy_rating']}/5 — {review['notes']}")

    # Write CSV
    os.makedirs(PROJECT_ROOT / "logs", exist_ok=True)
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    # Compute summary stats
    avg_rating     = sum(ratings) / len(ratings)
    score_5        = ratings.count(5)
    score_4        = ratings.count(4)
    score_3        = ratings.count(3)
    score_below_3  = sum(1 for r in ratings if r < 3)

    # Write summary report
    summary_lines = [
        "PIPELINE QUALITY SUMMARY REPORT",
        "=" * 40,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Questions Evaluated: {len(results)}",
        f"Successful Runs: {data['successful']}/{data['total']}",
        "",
        "--- Accuracy Rating Distribution ---",
        f"  Rating 5 (Citation + Simple Language): {score_5}",
        f"  Rating 4 (Citation present):           {score_4}",
        f"  Rating 3 (No citation):                {score_3}",
        f"  Rating <3 (Failed runs):               {score_below_3}",
        "",
        f"Average Accuracy Rating: {avg_rating:.2f} / 5.00",
        "",
        "--- Category Breakdown ---",
    ]

    for cat in ["PPC", "Constitution", "CrPC"]:
        cat_ratings = [r["accuracy_rating"] for r in rows if r["category"] == cat]
        cat_avg = sum(cat_ratings) / len(cat_ratings) if cat_ratings else 0
        summary_lines.append(f"  {cat:<15} Avg Rating: {cat_avg:.2f}  ({len(cat_ratings)} questions)")

    summary_lines += [
        "",
        "--- Overall Assessment ---",
        "Pipeline is functioning correctly." if avg_rating >= 4.0 else
        "Pipeline needs prompt or retrieval tuning.",
    ]

    with open(SUMMARY_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print("\n" + "=" * 65)
    print(f"Average Accuracy Rating: {avg_rating:.2f}/5.00")
    print(f"CSV log saved to:      {CSV_OUTPUT}")
    print(f"Summary saved to:      {SUMMARY_OUTPUT}")
    print("=" * 65)


if __name__ == "__main__":
    build_accuracy_log()
