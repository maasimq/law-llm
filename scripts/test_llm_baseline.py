"""
Baseline LLM Generation Test (No Retrieval)
=============================================
Tests raw LLM output on legal questions using the Groq API,
WITHOUT any retrieval-augmented context. This establishes a
performance baseline to later compare against the full RAG pipeline.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Legal questions spanning PPC, Constitution, and CrPC
BASELINE_QUESTIONS = [
    "What is the punishment for theft under the Pakistan Penal Code?",
    "What does Article 10 of the Constitution of Pakistan guarantee?",
    "Under what conditions can police arrest without a warrant under CrPC?",
    "What is the legal definition of Qatl-e-Amd (murder) in PPC?",
    "What fundamental rights does Article 14 of the Constitution protect?",
]

def test_raw_llm_generation():
    """
    Sends each baseline question directly to the Groq API (Llama 3.3 70B)
    without any retrieved context, and logs the raw responses.
    """
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "your_groq_api_key_here":
        print("ERROR: No valid GROQ_API_KEY found in .env file.")
        print("Please add your Groq API key to the .env file first.")
        return 1

    try:
        from groq import Groq
    except ImportError:
        print("ERROR: 'groq' package not installed. Run: pip install groq")
        return 1

    client = Groq(api_key=api_key)
    model_name = "llama-3.3-70b-versatile"

    print("=" * 60)
    print("BASELINE LLM GENERATION TEST (NO RETRIEVAL)")
    print(f"Model: {model_name}")
    print(f"Questions: {len(BASELINE_QUESTIONS)}")
    print("=" * 60)

    results = []

    for i, question in enumerate(BASELINE_QUESTIONS, 1):
        print(f"\n--- Question {i}/{len(BASELINE_QUESTIONS)} ---")
        print(f"Q: {question}\n")

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a legal assistant specializing in Pakistani law. "
                            "Answer the question accurately and concisely. "
                            "If you are unsure, state that clearly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                model=model_name,
                temperature=0.3,
                max_tokens=300,
            )

            answer = chat_completion.choices[0].message.content
            tokens_used = chat_completion.usage.total_tokens

            print(f"A: {answer}")
            print(f"[Tokens used: {tokens_used}]")

            results.append({
                "question": question,
                "answer": answer,
                "tokens_used": tokens_used,
                "model": model_name,
                "status": "success",
            })

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "question": question,
                "answer": None,
                "tokens_used": 0,
                "model": model_name,
                "status": f"error: {str(e)}",
            })

    # Save results to log file
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", "baseline_llm_test.json")
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "mode": "NO_RETRIEVAL (baseline)",
        "total_questions": len(BASELINE_QUESTIONS),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "results": results,
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Baseline test complete. {log_data['successful']}/{log_data['total_questions']} questions answered.")
    print(f"Results saved to: {log_path}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(test_raw_llm_generation())
