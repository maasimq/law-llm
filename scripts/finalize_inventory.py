#!/usr/bin/env python3
"""
Finalize legal document inventory by merging all sources into a unified master index.
Creates a consolidated data_index.csv that includes Constitution, CrPC, and future legal sources.
"""

import os
import csv
import re

def parse_section_number(sec):
    """Extract numeric part from section number for sorting."""
    match = re.match(r'(\d+)', str(sec))
    return int(match.group(1)) if match else 0

def finalize_inventory():
    """Merge all legal source indices into a unified master inventory."""
    
    print("\n" + "="*70)
    print("FINALIZING LEGAL DOCUMENT INVENTORY")
    print("="*70)
    
    # Setup paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    clean_dir = "data/clean"
    
    # Read existing indices
    print("\n[1/4] Reading source indices...")
    
    # Constitution index
    const_rows = []
    const_csv = os.path.join(clean_dir, "data_index.csv")
    if os.path.exists(const_csv):
        with open(const_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Standardize column names
                row['section_number'] = row.get('section_article_number') or row.get('section_number')
                row['title'] = row.get('title', '')
                row['source'] = 'Constitution of Pakistan, 1973'
                const_rows.append(row)
        print(f"  ✓ Constitution: {len(const_rows)} articles")
    else:
        print("  ⚠ Constitution index not found")
    
    # CrPC index
    crpc_rows = []
    crpc_csv = os.path.join(clean_dir, "crpc_index.csv")
    if os.path.exists(crpc_csv):
        with open(crpc_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['source'] = 'Code of Criminal Procedure, 1898'
                crpc_rows.append(row)
        print(f"  ✓ CrPC: {len(crpc_rows)} sections")
    else:
        print("  ⚠ CrPC index not found")
    
    # Combine all sources
    print("\n[2/4] Merging indices...")
    
    all_rows = const_rows + crpc_rows
    
    # Sort by act and section number
    all_rows.sort(key=lambda x: (x['act_name'], parse_section_number(x['section_number']), str(x['section_number'])))
    
    print(f"  ✓ Combined {len(all_rows)} total entries")
    print(f"    - Constitution: {len(const_rows)} articles")
    print(f"    - CrPC: {len(crpc_rows)} sections")
    
    # Data quality checks
    print("\n[3/4] Running data quality checks...")
    
    # Check for missing values
    missing_count = 0
    for row in all_rows:
        for key in ['filename', 'act_name', 'section_number', 'word_count', 'source']:
            if not row.get(key):
                missing_count += 1
    
    if missing_count > 0:
        print(f"  ⚠ {missing_count} missing values found")
    else:
        print("  ✓ No missing values")
    
    # Check file existence
    missing_files = []
    for row in all_rows:
        filepath = os.path.join(clean_dir, row['filename'])
        if not os.path.exists(filepath):
            missing_files.append(row['filename'])
    
    if missing_files:
        print(f"  ⚠ {len(missing_files)} files referenced but not found:")
        for f in missing_files[:5]:
            print(f"    - {f}")
    else:
        print(f"  ✓ All {len(all_rows)} files exist")
    
    # Summary statistics
    print("\n[4/4] Inventory Summary:")
    print(f"  Total entries: {len(all_rows)}")
    
    total_words = sum(int(row.get('word_count', 0)) for row in all_rows)
    print(f"  Total word count: {total_words:,} words")
    
    if all_rows:
        avg_words = total_words / len(all_rows)
        print(f"  Average section length: {avg_words:.0f} words")
    
    # Group by act
    acts = {}
    for row in all_rows:
        act = row['act_name']
        if act not in acts:
            acts[act] = {'count': 0, 'words': 0}
        acts[act]['count'] += 1
        acts[act]['words'] += int(row.get('word_count', 0))
    
    for act, data in acts.items():
        print(f"\n  {act}:")
        print(f"    - Sections: {data['count']}")
        print(f"    - Total words: {data['words']:,}")
        if data['count'] > 0:
            print(f"    - Avg length: {data['words'] / data['count']:.0f} words")
    
    # Save master index
    print("\n" + "="*70)
    master_csv = os.path.join(clean_dir, "master_inventory.csv")
    
    fieldnames = ['filename', 'act_name', 'section_number', 'title', 'word_count', 'source']
    with open(master_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            # Ensure all fields exist
            output_row = {field: row.get(field, '') for field in fieldnames}
            writer.writerow(output_row)
    
    print(f"✅ Master inventory saved: {master_csv}")
    print(f"   {len(all_rows)} total legal sections")
    print("="*70)
    
    # Summary for documentation
    print(f"\n📌 Inventory finalization complete:")
    print(f"   - Constitution articles: {len(const_rows)}")
    print(f"   - CrPC sections: {len(crpc_rows)}")
    print(f"   - Master file: master_inventory.csv")
    print(f"   - Location: {clean_dir}/")
    
    return 0


if __name__ == "__main__":
    finalize_inventory()
