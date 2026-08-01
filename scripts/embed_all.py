import os
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

CHUNKS_DIR = Path("data/chunks")
EMBEDDINGS_DIR = Path("data/embeddings")
MODEL_NAME = "BAAI/bge-small-en-v1.5"

def run():
    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, device='cpu')
    
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    txt_files = list(CHUNKS_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} chunks. Starting embedding generation...")
    
    for txt_file in tqdm(txt_files, desc="Embedding"):
        out_file = EMBEDDINGS_DIR / (txt_file.stem + ".npy")
        if out_file.exists():
            continue
            
        with open(txt_file, "r", encoding="utf-8") as f:
            text = f.read().strip()
            
        if not text:
            continue
            
        # Truncate at Illustrations header for embedding generation to prevent dilution
        embed_text = text.split("\nIllustrations")[0].split("\n\nIllustrations")[0] if "Illustrations" in text else text
        
        embedding = model.encode(embed_text, normalize_embeddings=True)
        np.save(out_file, embedding)
        
    print("All embeddings generated successfully!")

if __name__ == "__main__":
    run()
