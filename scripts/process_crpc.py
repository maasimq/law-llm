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
    Sections are identified by pattern: newline + number + period + space + title
    
    Returns list of dicts: [{number, title, text}, ...]
    """
    sections = []
    
    # Clean the raw text first
    text = strip_html_tags(raw_text)
    text = clean_whitespace(text)
    
    # Split by section markers: \n followed by digits (with optional letter) and period
    # Pattern: newline, one or more digits optionally followed by A-Z, period, space, then title text
    # We use positive lookahead to keep the section number
    parts = re.split(r'\n(?=\d+[A-Z]?\.?\s+)', text)
    
    for part in parts:
        part = part.strip()
        if not part or len(part) < 5:  # Skip empty or very short parts
            continue
        
        # Extract section number and title
        # Pattern: number (with optional letter) + period + title (until next sentence or newline)
        match = re.match(r'^(\d+[A-Z]?)\.\s+(.+?)(?:\n|$)', part, re.DOTALL)
        
        if match:
            sec_num = match.group(1).strip()
            title_text = match.group(2).strip()
            
            # Extract clean title (first sentence or line)
            # Take text until first period or newline with capital letter
            title_match = re.match(r'^([^.\n]*?)(?:\.|$)', title_text)
            if title_match:
                title = title_match.group(1).strip()
            else:
                # Fallback: take first 50 chars or until newline
                title = title_text.split('\n')[0][:100].strip()
            
            # Skip entries that are just headers like "[Repealed.]" or "[Omitted.]"
            if title.lower() in ['[repealed.]', '[omitted.]', '[omitted.]', 'rep. by', '[']:
                continue
            
            sections.append({
                "number": sec_num,
                "title": title,
                "text": part,
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
        
        print(f"  ✓ {filename} ({word_count} words)")
    
    return saved


def main():
    """Main processing pipeline."""
    print("=" * 70)
    print("CrPC (Code of Criminal Procedure, 1898) Processing Pipeline")
    print("=" * 70)
    
    # Setup paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    crpc_file = os.path.join(os.path.expanduser("~"), "Downloads", "CrPC.txt")
    clean_dir = os.path.join("data", "clean")
    
    # Check if input file exists
    if not os.path.exists(crpc_file):
        print(f"\n❌ ERROR: CrPC.txt not found at {crpc_file}")
        return 1
    
    print(f"\n📄 Input file: {crpc_file}")
    print(f"📁 Output directory: {clean_dir}")
    
    # Read raw file
    print("\n[1/4] Reading raw CrPC file...")
    try:
        with open(crpc_file, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()
        print(f"  ✓ Loaded {len(raw_text):,} characters")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return 1
    
    # Parse sections
    print("\n[2/4] Parsing sections...")
    try:
        sections = parse_crpc_sections(raw_text)
        print(f"  ✓ Extracted {len(sections)} sections")
        if sections:
            print(f"    Range: Section {sections[0]['number']} to {sections[-1]['number']}")
    except Exception as e:
        print(f"  ❌ Error parsing sections: {e}")
        return 1
    
    # Save individual section files
    print("\n[3/4] Saving individual section files...")
    try:
        saved_records = save_sections(sections, clean_dir, "crpc_section")
        print(f"  ✓ Saved {len(saved_records)} files")
    except Exception as e:
        print(f"  ❌ Error saving sections: {e}")
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
        print(f"  ✓ Created {csv_file}")
    except Exception as e:
        print(f"  ❌ Error writing CSV: {e}")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ CrPC Processing Complete!")
    print(f"   {len(saved_records)} sections saved to {clean_dir}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
