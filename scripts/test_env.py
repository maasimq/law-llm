# Verify dependencies

import sys

def test_import(module_name, display_name=None):
    """Try to import a module and report its version."""
    display_name = display_name or module_name
    try:
        mod = __import__(module_name)
        version = getattr(mod, "__version__", "version not available")
        print(f"  [OK] {display_name:25s} — version {version}")
        return True
    except ImportError as e:
        print(f"  [FAIL] {display_name:25s} — IMPORT FAILED: {e}")
        return False

def main():
    print("Checking environment...")
    print(f"\n  Python version: {sys.version}\n")
    print("  Checking required libraries...\n")

    results = []
    results.append(test_import("chromadb", "ChromaDB"))
    results.append(test_import("sentence_transformers", "sentence-transformers"))
    results.append(test_import("groq", "Groq API Client"))
    results.append(test_import("streamlit", "Streamlit"))
    results.append(test_import("dotenv", "python-dotenv"))

    print()
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"  All {total} libraries verified.")
    else:
        print(f"  {passed}/{total} libraries passed.")
        print("  Run: pip install -r requirements.txt")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
