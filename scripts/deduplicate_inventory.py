#!/usr/bin/env python3
"""
Deduplicate master inventory by keeping only the primary entry per file.
Removes footnotes and amendments that may have been extracted as separate entries.
"""

import os
import csv

def deduplicate_inventory():
    """Remove duplicate filenames, keeping first (primary) entry only."""
    
    print("\n" + "="*70)
    print("DEDUPLICATING INVENTORY")
    print("="*70)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    clean_dir = "data/clean"
    master_csv = os.path.join(clean_dir, "master_inventory.csv")
    
    print(f"\n[1/2] Reading inventory...")
    
    # Read all rows
    all_rows = []
    with open(master_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    
    print(f"  ✓ Loaded {len(all_rows)} entries")
    
    # Deduplicate by filename (keep first occurrence)
    print(f"\n[2/2] Deduplicating...")
    
    seen_files = set()
    deduped_rows = []
    duplicates = 0
    
    for row in all_rows:
        filename = row['filename']
        if filename not in seen_files:
            deduped_rows.append(row)
            seen_files.add(filename)
        else:
            duplicates += 1
    
    print(f"  ✓ Removed {duplicates} duplicate entries")
    print(f"  ✓ Final inventory: {len(deduped_rows)} unique entries")
    
    # Save deduplicated inventory
    backup_csv = os.path.join(clean_dir, "master_inventory_backup.csv")
    os.rename(master_csv, backup_csv)
    
    fieldnames = ['filename', 'act_name', 'section_number', 'title', 'word_count', 'source']
    with open(master_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)
    
    print(f"\n" + "="*70)
    print(f"✅ Inventory deduplicated")
    print(f"   - Backup: master_inventory_backup.csv")
    print(f"   - Deduplicated: master_inventory.csv")
    print(f"   - Entries: {len(deduped_rows)}")
    print("="*70)
    
    # Breakdown by source
    print(f"\nBreakdown by legal source:")
    sources = {}
    for row in deduped_rows:
        source = row['source']
        sources[source] = sources.get(source, 0) + 1
    
    for source, count in sorted(sources.items()):
        print(f"  - {source}: {count} sections")
    
    return 0


if __name__ == "__main__":
    deduplicate_inventory()
