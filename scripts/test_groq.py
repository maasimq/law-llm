# Test Groq API connectivity

import os
import sys
from dotenv import load_dotenv

def main():
    print("Testing Groq API connectivity...")

    # Load environment variables from .env before checking for the API key.
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    # Bail out early if the key is missing or still a placeholder value.
    if not api_key or api_key == "your_groq_api_key_here":
        print("ERROR: No valid GROQ_API_KEY found.")
        print("  Steps to fix:")
        print("    1. Copy .env.example to .env")
        print("    2. Get a free API key from https://console.groq.com/")
        print("    3. Paste the key into your .env file")
        return 1

    print(f"\n  API Key found: {api_key[:8]}...{api_key[-4:]}")
    print("  Sending test prompt to Groq API...\n")

    try:
        from groq import Groq

        # Create a client with the loaded key and send a short chat request.
        client = Groq(api_key=api_key)

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful legal assistant. Keep answers very short."
                },
                {
                    "role": "user",
                    "content": "What is Section 302 of the Pakistan Penal Code about? Answer in one sentence."
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=100,
        )

        response = chat_completion.choices[0].message.content
        model_used = chat_completion.model

        # Print the model and response so the script can be used as a quick smoke test.
        print(f"  Model: {model_used}")
        print(f"  Response: {response}")
        print("Groq API connection successful.")
        return 0

    except Exception as e:
        # Surface any API or network error without hiding the original exception.
        print(f"API call failed: {e}")
        print("\n  Check your API key and internet connection.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
