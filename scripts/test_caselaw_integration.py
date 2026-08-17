"""
End-to-End Integration Test for Case Law / Judicial Precedents Pipeline.
Tests retrieval, filtering, prompt injection, and LLM answer generation.
"""
import sys
import os
import json
from pathlib import Path

# Setup path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
os.chdir(str(Path(__file__).resolve().parent.parent))

from rag_pipeline import (
    retrieve_case_precedents,
    filter_cited_cases,
    build_rag_prompt,
    answer_question,
)


def separator(label):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")


def test_chromadb_collection():
    """Test 1: Verify ChromaDB caselaw_collection has the expected 100 items."""
    separator("TEST 1: ChromaDB caselaw_collection integrity")
    import chromadb
    db_path = Path("data/chroma_db")
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_collection(name="caselaw_collection")
    count = collection.count()
    print(f"  Collection count: {count}")
    assert count == 100, f"Expected 100 cases, got {count}"
    
    # Verify key metadata fields exist
    sample = collection.get(ids=["case_pld_2018_sc_595"])
    assert sample and sample["metadatas"], "Missing Sughran Bibi case"
    meta = sample["metadatas"][0]
    assert meta["citation"] == "PLD 2018 SC 595"
    assert "second" in meta["ratio_decidendi"].lower() or "fir" in meta["ratio_decidendi"].lower()
    
    # Verify Toheen-e-Risalat landmark case exists
    sample_blasphemy = collection.get(ids=["case_pld_2019_sc_64"])
    assert sample_blasphemy and sample_blasphemy["metadatas"], "Missing Asia Bibi landmark case"
    meta_b = sample_blasphemy["metadatas"][0]
    assert "295-C" in meta_b["statutes_cited"] or "295-c" in meta_b["ratio_decidendi"].lower()
    
    print(f"  Sample cases verified: {meta['citation']} and {meta_b['citation']}")
    print("  [PASSED]")


def test_retrieve_case_precedents():
    """Test 2: Semantic retrieval returns relevant cases for various query types."""
    separator("TEST 2: retrieve_case_precedents (semantic + exact)")

    # Test A: Bail query should return bail-related precedents
    bail_cases = retrieve_case_precedents("Can accused get bail if FIR is delayed in murder case?", n_results=3)
    print(f"\n  Query: 'bail if FIR is delayed in murder case'")
    print(f"  Retrieved {len(bail_cases)} cases:")
    for c in bail_cases:
        print(f"    - {c['citation']}: {c['case_title']}")
    assert len(bail_cases) > 0, "No bail cases retrieved"
    bail_citations = [c["citation"] for c in bail_cases]
    assert any("SCMR" in c or "PLD" in c for c in bail_citations), "Expected SCMR/PLD citations"
    print("  [PASSED]")

    # Test B: Exact citation lookup
    exact_cases = retrieve_case_precedents("PLD 2018 SC 595", n_results=2)
    print(f"\n  Query: 'PLD 2018 SC 595' (exact citation)")
    print(f"  Retrieved {len(exact_cases)} cases:")
    for c in exact_cases:
        print(f"    - {c['citation']}: {c['case_title']}")
    assert any(c["citation"] == "PLD 2018 SC 595" for c in exact_cases), "Exact citation not found"
    print("  [PASSED]")

    # Test C: Murder/evidence query
    murder_cases = retrieve_case_precedents("medical evidence vs eyewitness conflict in murder trial", n_results=2)
    print(f"\n  Query: 'medical evidence vs eyewitness conflict in murder trial'")
    print(f"  Retrieved {len(murder_cases)} cases:")
    for c in murder_cases:
        print(f"    - {c['citation']}: {c['case_title']}")
    assert len(murder_cases) > 0, "No murder/evidence cases retrieved"
    print("  [PASSED]")


def test_filter_cited_cases():
    """Test 3: filter_cited_cases correctly identifies cited vs. uncited cases."""
    separator("TEST 3: filter_cited_cases")

    mock_cases = [
        {"citation": "2022 SCMR 1420", "case_title": "Muhammad Akram v. The State"},
        {"citation": "PLD 2020 SC 556", "case_title": "Tariq Bashir v. The State"},
    ]

    # Answer that explicitly mentions the citation
    answer_with_cite = "Under Section 497(2) CrPC, as held in 2022 SCMR 1420, bail is available when FIR delay exceeds 24 hours."
    filtered = filter_cited_cases(answer_with_cite, mock_cases)
    print(f"  Answer mentions '2022 SCMR 1420' -> Filtered: {[c['citation'] for c in filtered]}")
    assert len(filtered) >= 1, "Should have found cited case"
    print("  [PASSED]")

    # Answer about bail (keyword match fallback)
    answer_bail = "Bail is a right in non-bailable offences under Section 497."
    filtered2 = filter_cited_cases(answer_bail, mock_cases)
    print(f"  Answer mentions 'bail'/'497' -> Filtered: {[c['citation'] for c in filtered2]}")
    assert len(filtered2) >= 1, "Keyword fallback should return at least 1 case"
    print("  [PASSED]")


def test_build_rag_prompt_with_precedents():
    """Test 4: build_rag_prompt correctly injects case law into context block."""
    separator("TEST 4: build_rag_prompt with case_precedents injection")

    mock_docs = ["Section 497 CrPC: An offence not falling within..."]
    mock_cases = [
        {
            "citation": "2022 SCMR 1420",
            "case_title": "Muhammad Akram v. The State",
            "court": "Supreme Court of Pakistan",
            "year": 2022,
            "statutes_cited": "CrPC - Section 497; PPC - Section 302",
            "ratio_decidendi": "Delayed FIR entitles accused to bail.",
            "urdu_ratio": "تاخیر سے ایف آئی آر",
            "facts_summary": "FIR was delayed 36 hours.",
            "disposition": "Bail Allowed",
        }
    ]

    prompt = build_rag_prompt("Can I get bail?", mock_docs, mode="advocate", case_precedents=mock_cases)
    assert "JUDICIAL PRECEDENT" in prompt, "Missing JUDICIAL PRECEDENT header"
    assert "2022 SCMR 1420" in prompt, "Missing citation in prompt"
    assert "Ratio Decidendi" in prompt, "Missing Ratio Decidendi"
    assert "Delayed FIR" in prompt, "Missing ratio content"
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Contains 'JUDICIAL PRECEDENT': True")
    print(f"  Contains '2022 SCMR 1420': True")
    print(f"  Contains 'Ratio Decidendi': True")
    print("  [PASSED]")


def test_answer_question_returns_4_tuple():
    """Test 5: answer_question returns (answer, docs, urdu_verified, case_precedents)."""
    separator("TEST 5: answer_question returns 4-tuple with case precedents")

    result = answer_question(
        "What are grounds for post-arrest bail in murder case?",
        mode="advocate"
    )
    assert len(result) == 4, f"Expected 4-tuple, got {len(result)}-tuple"
    answer, docs, urdu_verified, cases = result

    print(f"  Answer length: {len(answer)} chars")
    print(f"  Statutory docs retrieved: {len(docs)}")
    print(f"  Urdu verified: {urdu_verified}")
    print(f"  Case precedents: {len(cases)}")
    for c in cases:
        print(f"    - {c['citation']}: {c['case_title']}")

    assert len(answer) > 100, "Answer too short"
    assert isinstance(urdu_verified, bool), "urdu_verified should be bool"
    assert isinstance(cases, list), "cases should be list"
    print("  [PASSED]")


def test_answer_question_second_fir():
    """Test 6: Specific query about second FIR should cite Sughran Bibi."""
    separator("TEST 6: Second FIR query retrieves Sughran Bibi precedent")

    result = answer_question(
        "Can police register a second FIR for the same incident?",
        mode="advocate"
    )
    answer, docs, urdu_verified, cases = result
    case_citations = [c["citation"] for c in cases]

    print(f"  Answer snippet: {answer[:200]}...")
    print(f"  Case precedents: {case_citations}")
    # PLD 2018 SC 595 (Sughran Bibi) should be retrieved
    assert any("PLD 2018" in c for c in case_citations) or "sughran" in answer.lower() or "second fir" in answer.lower(), \
        "Expected Sughran Bibi or second FIR reference"
    print("  [PASSED]")


def test_answer_question_cheque_dishonor():
    """Test 7: Cheque dishonor query should cite 489-F precedents."""
    separator("TEST 7: Cheque dishonor 489-F query")

    result = answer_question(
        "What are the ingredients of offence under Section 489-F PPC for dishonored cheque?",
        mode="advocate"
    )
    answer, docs, urdu_verified, cases = result
    case_citations = [c["citation"] for c in cases]

    print(f"  Answer snippet: {answer[:200]}...")
    print(f"  Case precedents: {case_citations}")
    assert "489" in answer, "Answer should mention Section 489-F"
    print("  [PASSED]")


def test_conversational_returns_empty_cases():
    """Test 8: Conversational queries should return empty case list."""
    separator("TEST 8: Conversational query returns empty cases")

    # is_conversational() requires <= 3 words, so use a short greeting
    result = answer_question("Hello", mode="layman")
    answer, docs, urdu_verified, cases = result

    print(f"  Query: 'Hello'")
    print(f"  Cases returned: {len(cases)}")
    assert cases == [], f"Expected empty cases for conversational query, got {len(cases)}"
    print("  [PASSED]")


def test_caselaw_data_json_integrity():
    """Test 9: Verify caselaw_data.json structural integrity."""
    separator("TEST 9: caselaw_data.json data integrity")

    with open("data/caselaw_data.json", "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"  Total cases: {len(cases)}")
    assert len(cases) == 100, f"Expected 100 cases, got {len(cases)}"

    required_fields = ["id", "citation", "case_title", "court", "year", "statutes_cited",
                       "legal_topics", "ratio_decidendi", "facts_summary", "disposition", "urdu_ratio"]

    for i, case in enumerate(cases):
        for field in required_fields:
            assert field in case, f"Case {i} ({case.get('citation', 'unknown')}) missing field: {field}"
        assert isinstance(case["statutes_cited"], list), f"statutes_cited should be list in case {i}"
        assert isinstance(case["legal_topics"], list), f"legal_topics should be list in case {i}"
        assert case["year"] >= 2000, f"Year {case['year']} seems too old in case {i}"

    # Check unique citations
    citations = [c["citation"] for c in cases]
    assert len(citations) == len(set(citations)), "Duplicate citations found!"

    # Check coverage
    all_topics = set()
    for c in cases:
        all_topics.update(c["legal_topics"])
    print(f"  Unique legal topics covered: {len(all_topics)}")
    print(f"  Sample topics: {list(all_topics)[:8]}")
    assert len(all_topics) >= 10, "Should cover at least 10 unique legal topics"
    print("  [PASSED]")


def test_answer_question_toheen_e_risalat():
    """Test 10: Toheen-e-Risalat / Section 295-C PPC query should cite Asia Bibi / SP investigation rulings."""
    separator("TEST 10: Toheen-e-Risalat (Blasphemy) & Section 295-C PPC query")

    result = answer_question(
        "What is the standard of proof and procedure for investigation in Toheen e Risalat Section 295-C PPC case?",
        mode="advocate"
    )
    answer, docs, urdu_verified, cases = result
    case_citations = [c["citation"] for c in cases]

    print(f"  Answer snippet: {answer[:250]}...")
    print(f"  Case precedents retrieved: {case_citations}")
    assert any("2019" in c or "2022" in c or "2016" in c or "2002" in c for c in case_citations) or "295" in answer.lower(), \
        "Expected Toheen-e-Risalat precedent or Section 295-C statutory citations"
    print("  [PASSED]")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  LAW LLM — CASE LAW END-TO-END INTEGRATION TEST SUITE")
    print("="*70)

    passed = 0
    failed = 0
    errors = []

    tests = [
        test_caselaw_data_json_integrity,
        test_chromadb_collection,
        test_retrieve_case_precedents,
        test_filter_cited_cases,
        test_build_rag_prompt_with_precedents,
        test_answer_question_returns_4_tuple,
        test_answer_question_second_fir,
        test_answer_question_cheque_dishonor,
        test_answer_question_toheen_e_risalat,
        test_conversational_returns_empty_cases,
    ]

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((test_fn.__name__, str(e)))
            print(f"  [FAILED] {e}")

    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed} passed / {failed} failed / {len(tests)} total")
    print(f"{'='*70}")

    if errors:
        print("\n  FAILURES:")
        for name, err in errors:
            print(f"    - {name}: {err}")

    sys.exit(0 if failed == 0 else 1)
