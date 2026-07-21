import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables (API Key)
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

def ask_groq(question: str) -> str:
    """
    Sends a plain question to the Groq LLM without any retrieval.
    Used for Day 13 baseline testing.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            model=MODEL_NAME,
            temperature=0.3,
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def run_tests():
    print("Day 13 Checkpoint: Testing 5 Plain Questions (No Retrieval)\n" + "="*60)
    
    # 5 Sample Questions about the Constitution
    test_questions = [
        "What is the capital of Pakistan?",
        "What is Article 9 of the Constitution of Pakistan?",
        "Can a person be arrested without being informed of the grounds?",
        "Does the Constitution of Pakistan allow forced labor?",
        "What is the right to education in Pakistan?"
    ]

    log_lines = [
        "LLM Call Log (No Retrieval)",
        "===========================",
        f"Model: {MODEL_NAME}",
        ""
    ]

    for idx, question in enumerate(test_questions, 1):
        print(f"Q{idx}: {question}")
        answer = ask_groq(question)
        print(f"A: {answer}\n")
        
        log_lines.append(f"Question {idx}: {question}")
        log_lines.append(f"Answer: {answer}")
        log_lines.append("-" * 40 + "\n")

    # Save log file
    log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "llm_baseline_log.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
        
    print(f"[OK] Baseline answers saved to: {log_path}")

if __name__ == "__main__":
    run_tests()
