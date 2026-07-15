import os
import csv

def chunk_text(text, max_words=500, overlap=50):
    words = text.split()
    chunks = []
    
    # If the text is already small enough, return it as a single chunk
    if len(words) <= max_words:
        return [text]
    
    # Otherwise, split with overlap
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        
        # If we've reached the end, break
        if end == len(words):
            break
            
        # Move start forward, but keep an overlap
        start += (max_words - overlap)
        
    return chunks

def process_chunking():
    clean_dir = os.path.join("data", "clean")
    chunks_dir = os.path.join("data", "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    
    index_file = os.path.join(clean_dir, "data_index.csv")
    chunk_index_file = os.path.join(chunks_dir, "chunk_index.csv")
    
    if not os.path.exists(index_file):
        print(f"Error: {index_file} not found. Please complete cleaning first.")
        return
        
    with open(index_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        files_to_process = list(reader)
        
    with open(chunk_index_file, 'w', newline='', encoding='utf-8') as out_f:
        # We add chunk_id to keep track of which part of the article this is
        fieldnames = ['chunk_filename', 'original_filename', 'act_name', 'section_article_number', 'chunk_id', 'word_count']
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in files_to_process:
            orig_filename = row['filename']
            act_name = row['act_name']
            sec_num = row['section_article_number']
            
            filepath = os.path.join(clean_dir, orig_filename)
            if not os.path.exists(filepath):
                continue
                
            with open(filepath, 'r', encoding='utf-8') as text_f:
                text = text_f.read()
                
            # Create chunks (500 words max, 50 word overlap)
            chunks = chunk_text(text, max_words=500, overlap=50)
            
            for i, chunk in enumerate(chunks):
                # chunk_filename: e.g., constitution_article_10_chunk_0.txt
                base_name = os.path.splitext(orig_filename)[0]
                chunk_filename = f"{base_name}_chunk_{i}.txt"
                chunk_filepath = os.path.join(chunks_dir, chunk_filename)
                
                with open(chunk_filepath, 'w', encoding='utf-8') as c_f:
                    c_f.write(chunk)
                    
                chunk_word_count = len(chunk.split())
                
                writer.writerow({
                    'chunk_filename': chunk_filename,
                    'original_filename': orig_filename,
                    'act_name': act_name,
                    'section_article_number': sec_num,
                    'chunk_id': i,
                    'word_count': chunk_word_count
                })
                
                print(f"Saved {chunk_filename} (Words: {chunk_word_count})")
                
    print("\nChunking Complete! All files saved in /data/chunks")

if __name__ == "__main__":
    process_chunking()
