import os
import csv
import json
import numpy as np
import chromadb
from tqdm import tqdm

def load_and_ingest():
    print("Initializing ChromaDB Persistent Client...")
    
    # Create the chroma database directory if it doesn't exist
    db_path = os.path.join("data", "chroma_db")
    os.makedirs(db_path, exist_ok=True)
    
    # Persistent client saves everything to disk
    client = chromadb.PersistentClient(path=db_path)
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="law_collection",
        metadata={"hnsw:space": "cosine"} # bge-small-en-v1.5 works best with cosine similarity
    )

    index_files = [
        os.path.join("data", "embeddings", "embedding_index.csv"),
        os.path.join("data", "embeddings", "crpc_embedding_index.csv")
    ]
    
    total_inserted = 0
    
    for index_file in index_files:
        if not os.path.exists(index_file):
            print(f"Skipping {index_file}, not found.")
            continue
            
        print(f"\nProcessing index: {index_file}")
        with open(index_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            # Progress bar for visual tracking
            for row in tqdm(rows, desc="Ingesting to ChromaDB"):
                chunk_filename = row['chunk_filename']
                emb_filename = row['embedding_filename']
                
                chunk_path = os.path.join("data", "chunks", chunk_filename)
                emb_path = os.path.join("data", "embeddings", emb_filename)
                
                if not os.path.exists(chunk_path) or not os.path.exists(emb_path):
                    continue
                    
                # Read vector array and convert to native python list for ChromaDB
                emb = np.load(emb_path).tolist()
                
                # Read raw text content
                with open(chunk_path, 'r', encoding='utf-8') as tf:
                    text_content = tf.read()
                
                # Use chunk filename (without extension) as a unique UUID
                doc_id = chunk_filename.replace('.txt', '')
                
                ids.append(doc_id)
                embeddings.append(emb)
                documents.append(text_content)
                metadatas.append({
                    "act_name": row["act_name"],
                    "section_article_number": row["section_article_number"],
                    "chunk_id": int(row["chunk_id"]),
                    "word_count": int(row["word_count"])
                })
                
                # Batch insert every 200 documents to optimize memory
                if len(ids) >= 200:
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas
                    )
                    total_inserted += len(ids)
                    # Reset buffers
                    ids, embeddings, documents, metadatas = [], [], [], []
            
            # Insert any remaining documents
            if len(ids) > 0:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                total_inserted += len(ids)

    print(f"\n✅ Successfully ingested {total_inserted} chunks into ChromaDB.")
    print(f"📊 Total documents currently in collection: {collection.count()}")

if __name__ == "__main__":
    load_and_ingest()
