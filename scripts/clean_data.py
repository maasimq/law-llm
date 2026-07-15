# ==============================================================================
# LEGAL DOCUMENT CLEANING PIPELINE
# ==============================================================================
# Extracts individual legal sections/articles from raw HTML documents
# (Pakistan Penal Code, Code of Criminal Procedure, Constitution).
# Cleans HTML formatting, normalizes whitespace, and saves as structured text files.

import os
import re
import csv
import sys
import html


def strip_html_tags(text):
    """Remove all HTML tags and decode HTML entities.
    
    Steps:
    1. Remove <script> and <style> blocks (no text content)
    2. Remove HTML comments
    3. Convert <br> to newlines
    4. Convert <p> tags to double newlines for paragraph spacing
    5. Remove remaining HTML tags
    6. Decode HTML entities (e.g., &nbsp; -> space)
    """
    # Remove JavaScript blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove CSS style blocks
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Convert line breaks to newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    # Convert opening <p> tags to double newlines (paragraph breaks)
    text = re.sub(r'<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    # Remove closing </p> tags
    text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
    # Convert <hr> (horizontal rules) to visual separator
    text = re.sub(r'<hr[^>]*>', '\n---\n', text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities (e.g., &nbsp;, &quot;, &amp;)
    text = html.unescape(text)
    return text


def clean_whitespace(text):
    """Normalize whitespace: strip lines, collapse multiple blank lines.
    
    Steps:
    1. Split text into lines
    2. Strip leading/trailing whitespace from each line
    3. Join cleaned lines back together
    4. Collapse 3+ consecutive newlines into 2 (single blank line)
    5. Strip overall text
    """
    # Split text into individual lines
    lines = text.split('\n')
    cleaned = []
    # Remove leading and trailing whitespace from each line
    for line in lines:
        stripped = line.strip()
        cleaned.append(stripped)
    # Rejoin all lines
    result = '\n'.join(cleaned)
    # Collapse multiple consecutive blank lines into a single blank line
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def extract_ppc_sections(raw_html):
    """
    Extract individual sections from the Pakistan Penal Code HTML.
    Returns a list of dicts: [{number, title, text, chapter}, ...]
    
    Uses regex patterns to find:
    - Chapter headers (CHAPTER I, II, etc.) with titles
    - Section numbers and their content in <td> tags
    """
    sections = []
    current_chapter = "INTRODUCTION"  # Default chapter name
    
    # Regex to match chapter headers: <h4>CHAPTER I</h4><h4>Chapter Title</h4>
    chapter_pattern = re.compile(
        r'<h4[^>]*>\s*(CHAPTER\s+[IVXLCDM]+)\s*</h4>\s*<h4[^>]*>\s*(.*?)\s*</h4>',
        re.IGNORECASE | re.DOTALL
    )
    # Regex to match section: <nobr><b>123.</b></nobr> ... <td>section content</td>
    section_pattern = re.compile(
        r'<nobr><b>(\d+[A-Z]?)\.</b></nobr>.*?<td[^>]*>(.*?)</td>',
        re.DOTALL | re.IGNORECASE
    )
    # Find all chapter headers and store their positions in the HTML
    chapter_matches = list(chapter_pattern.finditer(raw_html))
    # Create list of (start_position, chapter_number, chapter_title)
    chapter_positions = [(m.start(), m.group(1).strip(), m.group(2).strip())
                         for m in chapter_matches]
    
    # Iterate through all sections in the HTML
    for match in section_pattern.finditer(raw_html):
        sec_num = match.group(1).strip()  # Section number (e.g., "123", "123A")
        sec_content = match.group(2).strip()  # Raw HTML content
        sec_pos = match.start()  # Position in HTML string
        
        # Determine which chapter this section belongs to
        # by comparing section position with chapter positions
        for i, (cpos, cnum, ctitle) in enumerate(chapter_positions):
            if i + 1 < len(chapter_positions):
                # Check if section is between this chapter and the next
                if cpos <= sec_pos < chapter_positions[i + 1][0]:
                    current_chapter = f"{cnum} — {ctitle}"
                    break
            else:
                # This is the last chapter, so any section after it belongs here
                if cpos <= sec_pos:
                    current_chapter = f"{cnum} — {ctitle}"
        
        # Clean the HTML content
        clean_content = strip_html_tags(sec_content)
        clean_content = clean_whitespace(clean_content)
        
        # Extract title from first sentence (ends with period and newline)
        title_match = re.match(r'^(.*?\.)\s*\n', clean_content)
        title = title_match.group(1).strip() if title_match else f"Section {sec_num}"

        # Store the section with metadata
        sections.append({
            "number": sec_num,
            "title": title,
            "text": clean_content,
            "chapter": current_chapter,
            "act": "Pakistan Penal Code, 1860"
        })

    return sections


def extract_constitution_articles(raw_html):
    """
    Extract individual articles from the Constitution HTML (Part II, Chapter 1).
    Only extracts Articles 8-28 (Fundamental Rights).
    Returns a list of dicts: [{number, title, text}, ...]
    
    Handles two possible HTML formats:
    1. With named anchors: <a name="8"></a>
    2. Without named anchors: just <nobr><b>8.</b></nobr>
    """
    articles = []
    
    # Regex to match articles with HTML anchors: <a name="8"></a><nobr><b>8.</b></nobr>...
    article_pattern = re.compile(
        r'<a\s+name="(\d+[A-Z]?)"\s*></a>.*?'
        r'<nobr><b>(\d+[A-Z]?)\.</b></nobr>.*?<td[^>]*>(.*?)</td>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Try the anchor-based pattern first; fall back to simpler pattern if not found
    if not article_pattern.findall(raw_html):
        # Fallback pattern without anchor tags: just <nobr><b>8.</b></nobr>...
        article_pattern = re.compile(
            r'<nobr><b>(\d+[A-Z]?)\.</b></nobr>.*?<td[^>]*>(.*?)</td>',
            re.DOTALL | re.IGNORECASE
        )
        # Extract articles using fallback pattern
        for match in article_pattern.finditer(raw_html):
            art_num = match.group(1).strip()  # Article number (e.g., "8", "8A")
            art_content = match.group(2).strip()  # Raw HTML content
            
            # Filter: only keep Articles 8-28 (Fundamental Rights section)
            try:
                # Extract numeric part to check range
                num_val = int(re.match(r'(\d+)', art_num).group(1))
                # Skip if outside Fundamental Rights range
                if num_val < 8 or num_val > 28:
                    continue
            except (ValueError, AttributeError):
                continue  # Skip if number extraction fails

            # Clean HTML formatting
            clean_content = strip_html_tags(art_content)
            clean_content = clean_whitespace(clean_content)

            # Extract title from first sentence
            title_match = re.match(r'^(.*?\.)\s', clean_content)
            title = title_match.group(1).strip() if title_match else f"Article {art_num}"

            # Store article with metadata
            articles.append({
                "number": art_num,
                "title": title,
                "text": clean_content,
                "chapter": "Part II, Chapter 1: Fundamental Rights",
                "act": "Constitution of Pakistan, 1973"
            })
    
    # If anchor pattern found matches, use it instead (else branch)
    # Extract using the anchor-based pattern (primary format)
    else:
        for match in article_pattern.finditer(raw_html):
            # Determine which group has the article number (may be group 1 or 2)
            art_num = match.group(2).strip() if match.lastindex >= 2 else match.group(1).strip()
            # Content is always the last matched group
            art_content = match.group(match.lastindex).strip()

            # Filter: only keep Articles 8-28 (Fundamental Rights)
            try:
                num_val = int(re.match(r'(\d+)', art_num).group(1))
                if num_val < 8 or num_val > 28:
                    continue
            except (ValueError, AttributeError):
                continue  # Skip if number extraction fails

            # Clean HTML formatting
            clean_content = strip_html_tags(art_content)
            clean_content = clean_whitespace(clean_content)

            # Extract title from first sentence
            title_match = re.match(r'^(.*?\.)\s', clean_content)
            title = title_match.group(1).strip() if title_match else f"Article {art_num}"

            # Store article with metadata
            articles.append({
                "number": art_num,
                "title": title,
                "text": clean_content,
                "chapter": "Part II, Chapter 1: Fundamental Rights",
                "act": "Constitution of Pakistan, 1973"
            })

    return articles


def process_raw_text_fallback(raw_html, act_name, prefix):
    """
    Fallback: if HTML parsing doesn't work well, just do basic
    text extraction and split by Section/Article markers.
    """
    text = strip_html_tags(raw_html)
    text = clean_whitespace(text)

    sections = []
    parts = re.split(r'\n(?=\d+[A-Z]?\.\s+[A-Z])', text)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        sec_match = re.match(r'^(\d+[A-Z]?)\.\s+(.*?)(?:\.\s|\n)', part, re.DOTALL)
        if sec_match:
            sec_num = sec_match.group(1)
            title = sec_match.group(2).strip()
            sections.append({
                "number": sec_num,
                "title": f"{title}.",
                "text": part,
                "chapter": "",
                "act": act_name
            })

    return sections


def save_sections(sections, output_dir, prefix):
    """Save each section/article as an individual .txt file.
    
    Args:
        sections: List of section dicts with {number, title, text, chapter, act}
        output_dir: Directory to save files in
        prefix: Filename prefix (e.g., 'ppc_section', 'constitution_article')
    
    Returns:
        List of metadata dicts for each saved section (for CSV index)
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    saved = []  # Metadata for index CSV

    # Save each section as a separate file
    for sec in sections:
        num = sec["number"]
        # Create filename: prefix_section_number.txt
        filename = f"{prefix}_{num}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Format file content with metadata header
        content = (
            f"ACT: {sec['act']}\n"
            f"SECTION/ARTICLE: {num}\n"
            f"TITLE: {sec['title']}\n"
            f"CHAPTER: {sec['chapter']}\n"
            f"{'=' * 60}\n\n"  # Visual separator
            f"{sec['text']}\n"
        )

        # Write file with UTF-8 encoding
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Calculate statistics for index
        word_count = len(sec["text"].split())
        # Store metadata (will be written to CSV later)
        saved.append({
            "filename": filename,
            "act": sec["act"],
            "section_article": num,
            "title": sec["title"],
            "chapter": sec["chapter"],
            "word_count": word_count
        })

    return saved


def main():
    """Main pipeline: process raw legal documents and save cleaned sections."""
    print("Cleaning legal data pipeline...")

    # Set working directory to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Create output directory
    clean_dir = "data/clean"
    os.makedirs(clean_dir, exist_ok=True)

    # Accumulate metadata for all sections across all acts
    all_records = []
    # ========== PROCESS PAKISTAN PENAL CODE ==========
    # Find all PPC files in raw directory
    ppc_files = [
        os.path.join("data", "raw", "ppc", f)
        for f in os.listdir(os.path.join("data", "raw", "ppc"))
        if f.endswith((".html", ".htm", ".txt"))
    ] if os.path.isdir(os.path.join("data", "raw", "ppc")) else []

    if ppc_files:
        print("\n  Processing Pakistan Penal Code...")
        for fpath in ppc_files:
            # Read raw file
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            # Try HTML-specific extraction
            sections = extract_ppc_sections(raw)
            # Fall back to generic text extraction if no sections found
            if not sections:
                print(f"    [WARN] HTML parsing found 0 sections, trying fallback...")
                sections = process_raw_text_fallback(raw, "Pakistan Penal Code, 1860", "ppc")
            # Save sections as individual files
            records = save_sections(sections, clean_dir, "ppc_section")
            all_records.extend(records)
            print(f"    [OK] Extracted {len(records)} PPC sections")
    else:
        print("\n  [WARN] No PPC files found in data/raw/ppc/")
        print("     Run: python scripts/download_sources.py first")
    # ========== PROCESS CODE OF CRIMINAL PROCEDURE ==========
    # Find all CrPC files in raw directory
    crpc_files = [
        os.path.join("data", "raw", "crpc", f)
        for f in os.listdir(os.path.join("data", "raw", "crpc"))
        if f.endswith((".html", ".htm", ".txt"))
    ] if os.path.isdir(os.path.join("data", "raw", "crpc")) else []

    if crpc_files:
        print("\n  Processing Code of Criminal Procedure...")
        for fpath in crpc_files:
            # Read raw file
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            # Use generic fallback extraction (no CrPC-specific HTML structure defined)
            sections = process_raw_text_fallback(raw, "Code of Criminal Procedure, 1898", "crpc")
            # Save sections as individual files
            records = save_sections(sections, clean_dir, "crpc_section")
            all_records.extend(records)
            print(f"    [OK] Extracted {len(records)} CrPC sections")
    else:
        print("\n  [WARN] No CrPC files found in data/raw/crpc/")
        print("     Please download CrPC manually (see download_sources.py)")
    # ========== PROCESS CONSTITUTION ==========
    # Find all Constitution files in raw directory
    const_files = [
        os.path.join("data", "raw", "constitution", f)
        for f in os.listdir(os.path.join("data", "raw", "constitution"))
        if f.endswith((".html", ".htm", ".txt"))
    ] if os.path.isdir(os.path.join("data", "raw", "constitution")) else []

    if const_files:
        print("\n  Processing Constitution (Fundamental Rights)...")
        for fpath in const_files:
            # Read raw file
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            # Try Constitution-specific HTML extraction (Articles 8-28 only)
            articles = extract_constitution_articles(raw)
            # Fall back to generic text extraction if no articles found
            if not articles:
                print(f"    [WARN] HTML parsing found 0 articles, trying fallback...")
                articles = process_raw_text_fallback(
                    raw, "Constitution of Pakistan, 1973", "constitution"
                )
            # Save articles as individual files
            records = save_sections(articles, clean_dir, "constitution_article")
            all_records.extend(records)
            print(f"    [OK] Extracted {len(records)} Constitutional articles")
    else:
        print("\n  [WARN] No Constitution files found in data/raw/constitution/")
        print("     Run: python scripts/download_sources.py first")
    # ========== WRITE INDEX CSV ==========
    if all_records:
        # Create CSV index with metadata for all sections
        index_path = os.path.join("data", "data_index.csv")
        with open(index_path, "w", newline="", encoding="utf-8") as csvfile:
            # Define CSV columns
            writer = csv.DictWriter(csvfile, fieldnames=[
                "filename", "act", "section_article", "title", "chapter", "word_count"
            ])
            writer.writeheader()
            writer.writerows(all_records)

        # Print summary statistics
        print(f"\n  Data index saved: {index_path}")
        print(f"     Total records: {len(all_records)}")
        total_words = sum(r["word_count"] for r in all_records)
        print(f"     Total word count: {total_words:,}")
    else:
        print("\n  [FAIL] No records to write. Ensure raw data is present.")

    print()  # Final newline
    return 0 if all_records else 1


if __name__ == "__main__":
    sys.exit(main())
