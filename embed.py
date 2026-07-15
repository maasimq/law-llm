import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
LOGS_DIR = PROJECT_ROOT / "logs"
CHUNK_INDEX_FILE = CHUNKS_DIR / "crpc_chunk_index.csv"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
EXPECTED_DIMENSION = 384


def load_model():
    print(f"Loading embedding model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def load_chunk_rows(limit=None):
    if not CHUNK_INDEX_FILE.exists():
        raise FileNotFoundError(
            f"CrPC chunk index not found: {CHUNK_INDEX_FILE}"
        )

    with open(CHUNK_INDEX_FILE, "r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise FileNotFoundError(f"No rows found in {CHUNK_INDEX_FILE}")

    if limit is not None:
        rows = rows[:limit]

    return rows


def read_chunk_text(chunk_filename):
    chunk_path = CHUNKS_DIR / chunk_filename
    if not chunk_path.exists():
        raise FileNotFoundError(f"Chunk file not found: {chunk_path}")

    with open(chunk_path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def embedding_filename(chunk_filename):
    return Path(chunk_filename).stem + ".npy"


def save_embedding(chunk_filename, embedding):
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    output = EMBEDDINGS_DIR / embedding_filename(chunk_filename)
    np.save(output, embedding)
    return output


def write_log(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def run(limit=None, test_mode=False):
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if test_mode:
        limit = 5

    rows = load_chunk_rows(limit=limit)
    model = load_model()

    print(f"Embedding {len(rows)} CrPC chunk(s)...")

    index = []
    all_match = True

    for row in tqdm(rows, desc="CrPC embeddings"):
        chunk_filename = row["chunk_filename"]
        text = read_chunk_text(chunk_filename)
        embedding = model.encode(text, normalize_embeddings=True)

        if len(embedding) != EXPECTED_DIMENSION:
            all_match = False

        output_path = save_embedding(chunk_filename, embedding)
        index.append(
            {
                "embedding_filename": output_path.name,
                "chunk_filename": chunk_filename,
                "chunk_id": row.get("chunk_id", ""),
                "section_count": row.get("section_count", ""),
                "word_count": row.get("word_count", ""),
                "act_name": row.get("act_name", ""),
                "dimension": len(embedding),
            }
        )

    index_path = EMBEDDINGS_DIR / "crpc_embedding_index.json"
    with open(index_path, "w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=4)

    csv_path = EMBEDDINGS_DIR / "crpc_embedding_index.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        if index:
            writer = csv.DictWriter(handle, fieldnames=index[0].keys())
            writer.writeheader()
            writer.writerows(index)

    log_lines = [
        "CrPC Embedding Log",
        "==================",
        "",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Model: {MODEL_NAME}",
        f"Expected dimension: {EXPECTED_DIMENSION}",
        f"Chunks processed: {len(rows)}",
        f"All dimensions match: {'YES' if all_match else 'NO'}",
        "",
    ]
    for item in index:
        log_lines.append(
            f"{item['chunk_filename']} -> dim={item['dimension']}"
        )

    write_log(LOGS_DIR / "crpc_embedding.log", log_lines)

    print(f"CrPC embedding index saved to {index_path}")
    print(f"CrPC embedding CSV saved to {csv_path}")
    print(f"CrPC embedding log saved to {LOGS_DIR / 'crpc_embedding.log'}")

    return all_match and len(index) == len(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate CrPC embeddings")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Embed only the first 5 CrPC chunks.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Embed only the first N CrPC chunks.",
    )
    args = parser.parse_args()

    success = run(limit=args.limit, test_mode=args.test)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
