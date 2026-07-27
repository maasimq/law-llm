#!/usr/bin/env python3
"""
Parse and process the Code of Criminal Procedure (CrPC), 1898.
Splits the document into individual sections and saves them as clean text files.
"""

import os
import re
import csv
import sys


def strip_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def clean_whitespace(text):
    """Normalize whitespace: remove extra spaces, tabs, fix newlines."""
    # Replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with double newline (preserve paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def parse_crpc_sections(raw_text):
    """
    Parse CrPC text and extract individual sections.
    """
    sections = []
    
    # Skip the Table of Contents by finding where the actual law starts
    start_idx = raw_text.find("enacted as follows:")
    if start_idx != -1:
        raw_text = raw_text[start_idx:]
    
    text = strip_html_tags(raw_text)
    
    # Pattern: newline, optional spaces, section number, period, space, title
    pattern = re.compile(r'\n\s*(\d+[A-Z]?)\.\s+([^\n]+)')
    matches = list(pattern.finditer(text))
    
    for i in range(len(matches)):
        m = matches[i]
        sec_num = m.group(1).strip()
        title = m.group(2).strip()
        
        # The body is from the end of this match to the start of the next match
        body_start = m.end()
        body_end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        
        # The title sometimes continues into the body if it's long, or is just the first sentence
        full_text = m.group(0).strip() + "\n" + body
        full_text = clean_whitespace(full_text)
        
        if title.lower() in ['[repealed.]', '[omitted.]', 'rep. by', '[']:
            continue
            
        sections.append({
            "number": sec_num,
            "title": title[:100],  # Limit title length
            "text": full_text,
            "chapter": "",
            "act": "Code of Criminal Procedure, 1898"
        })
    
    return sections


def save_sections(sections, output_dir, prefix):
    """Save each section as an individual .txt file.
    
    Args:
        sections: List of section dicts with {number, title, text, chapter, act}
        output_dir: Directory to save files in
        prefix: Filename prefix (e.g., 'crpc_section')
    
    Returns:
        List of metadata dicts for each saved section (for CSV index)
    """
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    
    for sec in sections:
        num = sec["number"]
        filename = f"{prefix}_{num}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Format file content with metadata header
        content = (
            f"ACT: {sec['act']}\n"
            f"SECTION: {num}\n"
            f"TITLE: {sec['title']}\n"
            f"CHAPTER: {sec['chapter']}\n"
            f"{'=' * 60}\n\n"
            f"{sec['text']}\n"
        )
        
        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Calculate statistics
        word_count = len(sec["text"].split())
        
        saved.append({
            "filename": filename,
            "act_name": sec["act"],
            "section_number": num,
            "title": sec["title"],
            "word_count": word_count
        })
        
        print(f"   {filename} ({word_count} words)")
    
    return saved


def main():
    """Main processing pipeline."""
    print("=" * 70)
    print("CrPC (Code of Criminal Procedure, 1898) Processing Pipeline")
    print("=" * 70)
    
    # Setup paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    crpc_file = os.path.join("data", "raw", "crpc", "CrPC.txt")
    clean_dir = os.path.join("data", "clean")
    
    # Check if input file exists
    if not os.path.exists(crpc_file):
        print(f"\nERROR: CrPC.txt not found at {crpc_file}")
        return 1
    
    print(f"\n Input file: {crpc_file}")
    print(f" Output directory: {clean_dir}")
    
    # Read raw file
    print("\n[1/4] Reading raw CrPC file...")
    try:
        with open(crpc_file, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()
        print(f"   Loaded {len(raw_text):,} characters")
    except Exception as e:
        print(f"   Error reading file: {e}")
        return 1
    
    # Parse sections
    print("\n[2/4] Parsing sections...")
    try:
        sections = parse_crpc_sections(raw_text)
        print(f"   Extracted {len(sections)} sections")
        if sections:
            print(f"    Range: Section {sections[0]['number']} to {sections[-1]['number']}")
    except Exception as e:
        print(f"   Error parsing sections: {e}")
        return 1
    
    # Save individual section files
    print("\n[3/4] Saving individual section files...")
    try:
        saved_records = save_sections(sections, clean_dir, "crpc_section")
        print(f"   Saved {len(saved_records)} files")
    except Exception as e:
        print(f"   Error saving sections: {e}")
        return 1
    
    # Write index CSV
    print("\n[4/4] Creating index CSV...")
    try:
        csv_file = os.path.join(clean_dir, "crpc_index.csv")
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, 
                fieldnames=["filename", "act_name", "section_number", "title", "word_count"]
            )
            writer.writeheader()
            writer.writerows(saved_records)
        print(f"   Created {csv_file}")
    except Exception as e:
        print(f"   Error writing CSV: {e}")
        return 1
    
    print("\n" + "=" * 70)
    print(" CrPC Processing Complete!")
    print(f"   {len(saved_records)} sections saved to {clean_dir}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
