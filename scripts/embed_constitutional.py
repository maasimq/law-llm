import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Resolve paths from project root so the script works from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
LOGS_DIR = PROJECT_ROOT / "logs"
CHUNK_INDEX_FILE = CHUNKS_DIR / "chunk_index.csv"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EXPECTED_DIMENSION = 384


def load_model():
    print(f"\nLoading embedding model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def load_chunk_rows(limit=None):
    if not CHUNK_INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Chunk index not found: {CHUNK_INDEX_FILE}\n"
            "Run chunking.py first."
        )

    with open(CHUNK_INDEX_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise FileNotFoundError(f"No rows found in {CHUNK_INDEX_FILE}")

    if limit is not None:
        rows = rows[:limit]

    return rows


def read_chunk_text(chunk_filename):
    chunk_path = CHUNKS_DIR / chunk_filename
    if not chunk_path.exists():
        raise FileNotFoundError(f"Chunk file not found: {chunk_path}")

    with open(chunk_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def embedding_filename(chunk_filename):
    return Path(chunk_filename).stem + ".npy"


def save_embedding(chunk_filename, embedding):
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    output = EMBEDDINGS_DIR / embedding_filename(chunk_filename)
    np.save(output, embedding)
    return output


def write_log(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_embeddings(limit=None, test_mode=False):
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    model = load_model()

    all_rows = load_chunk_rows()
    total_chunks = len(all_rows)

    if test_mode:
        limit = 5

    rows = load_chunk_rows(limit=limit)
    mode = "TEST" if limit is not None else "FULL"

    embedded_count = 0
    all_match = True
    index = []

    print(f"\nEmbedding {len(rows)} chunk(s)...\n")

    for row in tqdm(rows):
        chunk_filename = row["chunk_filename"]
        text = read_chunk_text(chunk_filename)

        embedding = model.encode(text, normalize_embeddings=True)

        if len(embedding) != EXPECTED_DIMENSION:
            all_match = False

        output_file = save_embedding(chunk_filename, embedding)

        index.append(
            {
                "embedding_filename": output_file.name,
                "chunk_filename": chunk_filename,
                "original_filename": row.get("original_filename", ""),
                "act_name": row.get("act_name", ""),
                "section_article_number": row.get("section_article_number", ""),
                "chunk_id": row.get("chunk_id", ""),
                "word_count": row.get("word_count", ""),
                "dimension": len(embedding),
            }
        )

        embedded_count += 1

    embedding_index_file = EMBEDDINGS_DIR / "embedding_index.json"
    with open(embedding_index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    embedding_index_csv = EMBEDDINGS_DIR / "embedding_index.csv"
    with open(embedding_index_csv, "w", newline="", encoding="utf-8") as f:
        if index:
            writer = csv.DictWriter(f, fieldnames=index[0].keys())
            writer.writeheader()
            writer.writerows(index)

    on_disk_count = sum(
        1
        for row in all_rows
        if (EMBEDDINGS_DIR / embedding_filename(row["chunk_filename"])).exists()
    )

    checkpoint_ready = all_match and on_disk_count == total_chunks

    log_file = LOGS_DIR / "checkpoint5_log.txt"
    log_lines = [
        "Embedding Generation Log",
        "========================",
        "",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Mode: {mode}",
        f"Project root: {PROJECT_ROOT}",
        f"Model: {MODEL_NAME}",
        f"Expected dimension: {EXPECTED_DIMENSION}",
        f"Total chunks in index: {total_chunks}",
        f"Chunks processed this run: {embedded_count}",
        f"Total embeddings on disk: {on_disk_count}",
        f"Counts match: {'YES' if on_disk_count == total_chunks else 'NO'}",
        f"Dimensions match: {'YES' if all_match else 'NO'}",
        "",
        "Per-chunk verification:",
    ]

    for row in all_rows:
        emb_path = EMBEDDINGS_DIR / embedding_filename(row["chunk_filename"])
        if emb_path.exists():
            vector = np.load(emb_path)
            dim_ok = vector.shape[0] == EXPECTED_DIMENSION
            status = "OK" if dim_ok else "FAIL"
            log_lines.append(
                f"  [{status}] {row['chunk_filename']} -> dim={vector.shape[0]}"
            )
        else:
            log_lines.append(f"  [MISSING] {row['chunk_filename']}")

    log_lines.extend(
        [
            "",
            f"Checkpoint 5 ready: {'YES' if checkpoint_ready else 'NO'}",
        ]
    )
    write_log(log_file, log_lines)

    print(f"\nEmbedding index saved to {embedding_index_file}")
    print(f"Confirmation log saved to {log_file}")
    print(f"Embeddings folder: {EMBEDDINGS_DIR}")
    print(f"Embeddings on disk: {on_disk_count}/{total_chunks}")

    if checkpoint_ready:
        print("\nCheckpoint 5 criteria met.")
        print("All chunks embedded successfully.")
        print("Embedding dimension = 384")
    elif test_mode or limit is not None:
        print("\nTest batch complete.")
        print("Run from project root without --test to embed all chunks:")
        print("  python scripts/embed.py")
    else:
        print("\nWarning: embedding count or dimensions do not match.")

    return checkpoint_ready if limit is None else all_match and embedded_count == len(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for legal chunks"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Embed only the first 5 chunks.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Embed only the first N chunks.",
    )
    args = parser.parse_args()

    success = generate_embeddings(limit=args.limit, test_mode=args.test)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
