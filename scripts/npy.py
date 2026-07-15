from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"

emb_path = EMBEDDINGS_DIR / "constitution_article_8_chunk_0.npy"

if not emb_path.exists():
    print(f"File not found: {emb_path}")
    print("\nAvailable .npy files:")
    for f in sorted(EMBEDDINGS_DIR.glob("*.npy")):
        print(f"  {f.name}")
    raise SystemExit(1)

emb = np.load(emb_path)

print("File:", emb_path)
print("Shape:", emb.shape)
print("Dimension:", len(emb))
print("First 20 values:", emb[:20])
print("Min / Max:", emb.min(), emb.max())
