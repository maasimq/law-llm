import os
import chromadb
import numpy as np
from tqdm import tqdm

def get_metadata_from_filename(filename):
    """Extract act name and section/article number from filename."""
    if filename.startswith("constitution"):
        act = "Constitution of Pakistan"
        # constitution_article_10_chunk_0.txt -> 10
        parts = filename.replace("constitution_article_", "").split("_chunk")
        sec = parts[0].upper()
    elif filename.startswith("crpc"):
        act = "Code of Criminal Procedure, 1898"
        sec = "Unknown"  # the crpc chunking didn't put sections in filename
    elif filename.startswith("ppc"):
        act = "Pakistan Penal Code, 1860"
        # ppc_section_302_chunk_0.txt -> 302
        parts = filename.replace("ppc_section_", "").split("_chunk")
        sec = parts[0].upper()
    else:
        act = "Unknown"
        sec = "Unknown"
    return act, sec

def load_and_ingest():
    db_path = os.path.join("data", "chroma_db")
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    
    # Delete the existing collection so we can do a fresh, complete ingest
    try:
        client.delete_collection("law_collection")
    except Exception:
        pass
        
    collection = client.create_collection(
        name="law_collection",
        metadata={"hnsw:space": "cosine"}
    )

    chunks_dir = os.path.join("data", "chunks")
    embeddings_dir = os.path.join("data", "embeddings")
    
    txt_files = [f for f in os.listdir(chunks_dir) if f.endswith(".txt")]
    
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    total_inserted = 0
    
    print(f"Found {len(txt_files)} legal chunks on disk. Starting complete ingestion...")
    
    for filename in tqdm(txt_files, desc="Ingesting to ChromaDB"):
        chunk_path = os.path.join(chunks_dir, filename)
        emb_filename = filename.replace(".txt", ".npy")
        emb_path = os.path.join(embeddings_dir, emb_filename)
        
        if not os.path.exists(emb_path):
            continue
            
        with open(chunk_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
            
        emb = np.load(emb_path).tolist()
        
        act_name, sec_num = get_metadata_from_filename(filename)
        doc_id = filename.replace('.txt', '')
        
        ids.append(doc_id)
        embeddings.append(emb)
        documents.append(text_content)
        metadatas.append({
            "act_name": act_name,
            "section_article_number": sec_num
        })
        
        if len(ids) >= 200:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            total_inserted += len(ids)
            ids, embeddings, documents, metadatas = [], [], [], []
            
    if len(ids) > 0:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        total_inserted += len(ids)

    print(f"\nSuccessfully ingested {total_inserted} chunks into ChromaDB.")
    print(f"Total documents currently in collection: {collection.count()}")

if __name__ == "__main__":
    load_and_ingest()
