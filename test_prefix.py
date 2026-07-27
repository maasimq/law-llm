import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path='data/chroma_db')
collection = client.get_collection('law_collection')
model = SentenceTransformer('BAAI/bge-small-en-v1.5', device='cpu')

query = 'What is the punishment for theft?'

print('WITH PREFIX:')
emb_with = model.encode('Represent this sentence for searching relevant passages: ' + query, normalize_embeddings=True).tolist()
res_with = collection.query(query_embeddings=[emb_with], n_results=3)
for meta in res_with['metadatas'][0]: print(f"  {meta.get('act_name')} - {meta.get('section_article_number')}")

print('\nWITHOUT PREFIX:')
emb_without = model.encode(query, normalize_embeddings=True).tolist()
res_without = collection.query(query_embeddings=[emb_without], n_results=3)
for meta in res_without['metadatas'][0]: print(f"  {meta.get('act_name')} - {meta.get('section_article_number')}")
