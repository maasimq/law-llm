#!/usr/bin/env python3
"""
Chunk CrPC sections into ~500-word chunks aligned to section boundaries.
Does NOT chunk within a section - keeps sections together when possible.
"""

import os
import csv

def chunk_crpc_sections(inventory_csv, clean_dir, chunks_dir, max_words=500):
    """
    Process CrPC sections and create chunks aligned to section boundaries.
    
    Strategy:
    - Read sections in order
    - Accumulate sections until adding another would exceed max_words
    - When limit reached, save as a chunk
    - Start new chunk with the section that didn't fit
    - This respects section boundaries (no section is split)
    """
    
    if not os.path.exists(inventory_csv):
        print(f"❌ Inventory file not found: {inventory_csv}")
        return False
    
    os.makedirs(chunks_dir, exist_ok=True)
    
    print(f"\n{'='*70}")
    print("CHUNKING CrPC SECTIONS (500-word chunks, section-aligned)")
    print(f"{'='*70}\n")
    
    # Read inventory and filter for CrPC only
    crpc_files = []
    with open(inventory_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('source') and 'Code of Criminal Procedure' in row['source']:
                crpc_files.append(row)
    
    print(f"[1/3] Loading {len(crpc_files)} CrPC sections...")
    
    if not crpc_files:
        print("❌ No CrPC sections found in inventory")
        return False
    
    # Load section contents
    sections_data = []
    for row in crpc_files:
        filepath = os.path.join(clean_dir, row['filename'])
        if not os.path.exists(filepath):
            print(f"⚠ File not found: {row['filename']}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections_data.append({
                'filename': row['filename'],
                'section_num': row['section_number'],
                'title': row.get('title', ''),
                'content': content,
                'word_count': len(content.split())
            })
        except Exception as e:
            print(f"⚠ Error reading {row['filename']}: {e}")
            continue
    
    print(f"  ✓ Loaded {len(sections_data)} sections")
    
    # Create chunks aligned to section boundaries
    print(f"\n[2/3] Creating chunks (max {max_words} words per chunk)...")
    
    chunks = []
    current_chunk_sections = []
    current_chunk_words = 0
    chunk_counter = 0
    
    for i, section in enumerate(sections_data):
        section_words = section['word_count']
        
        # If adding this section would exceed limit and we have content:
        if current_chunk_words + section_words > max_words and current_chunk_sections:
            # Save current chunk
            chunks.append({
                'chunk_id': chunk_counter,
                'sections': current_chunk_sections,
                'word_count': current_chunk_words
            })
            chunk_counter += 1
            current_chunk_sections = []
            current_chunk_words = 0
        
        # Add section to current chunk
        current_chunk_sections.append(section)
        current_chunk_words += section_words
    
    # Don't forget the last chunk
    if current_chunk_sections:
        chunks.append({
            'chunk_id': chunk_counter,
            'sections': current_chunk_sections,
            'word_count': current_chunk_words
        })
    
    print(f"  ✓ Created {len(chunks)} chunks")
    
    # Save chunks and create index
    print(f"\n[3/3] Saving chunks...")
    
    chunk_index_file = os.path.join(chunks_dir, "crpc_chunk_index.csv")
    chunk_records = []
    
    for chunk in chunks:
        chunk_id = chunk['chunk_id']
        sections = chunk['sections']
        word_count = chunk['word_count']
        
        # Create chunk content: concatenate section contents
        chunk_content = ""
        section_nums = []
        section_filenames = []
        
        for section in sections:
            chunk_content += section['content'] + "\n\n"
            section_nums.append(section['section_num'])
            section_filenames.append(section['filename'])
        
        # Filename: crpc_chunk_<id>.txt
        chunk_filename = f"crpc_chunk_{chunk_id}.txt"
        chunk_filepath = os.path.join(chunks_dir, chunk_filename)
        
        # Save chunk file
        with open(chunk_filepath, 'w', encoding='utf-8') as f:
            f.write(chunk_content)
        
        # Create index record
        chunk_records.append({
            'chunk_filename': chunk_filename,
            'chunk_id': chunk_id,
            'sections_included': ','.join(section_nums),
            'section_count': len(sections),
            'original_files': ','.join(section_filenames),
            'word_count': word_count,
            'act_name': 'Code of Criminal Procedure, 1898'
        })
        
        print(f"  ✓ {chunk_filename}")
        print(f"    - Sections: {','.join(section_nums)}")
        print(f"    - Word count: {word_count}")
    
    # Write chunk index
    with open(chunk_index_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'chunk_filename',
            'chunk_id',
            'sections_included',
            'section_count',
            'original_files',
            'word_count',
            'act_name'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(chunk_records)
    
    # Print summary
    total_words = sum(c['word_count'] for c in chunks)
    avg_chunk_words = total_words / len(chunks) if chunks else 0
    
    print(f"\n{'='*70}")
    print("✅ CrPC CHUNKING COMPLETE")
    print(f"{'='*70}")
    print(f"  Chunks created: {len(chunks)}")
    print(f"  Total sections: {len(sections_data)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Average chunk size: {avg_chunk_words:.0f} words")
    print(f"  Chunk index: {chunk_index_file}")
    print(f"  Chunk directory: {chunks_dir}")
    print(f"{'='*70}\n")
    
    return True


def main():
    """Main entry point."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    clean_dir = os.path.join("data", "clean")
    chunks_dir = os.path.join("data", "chunks")
    inventory_csv = os.path.join(clean_dir, "master_inventory.csv")
    
    success = chunk_crpc_sections(inventory_csv, clean_dir, chunks_dir, max_words=500)
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
