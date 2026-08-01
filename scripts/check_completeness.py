import os
import re
from pathlib import Path

CHUNKS_DIR = Path("data/chunks")

def main():
    chunk_files = list(CHUNKS_DIR.glob("*.txt"))
    print(f"Total chunk files in data/chunks: {len(chunk_files)}")

    ppc_sections = set()
    crpc_sections = set()
    constitution_articles = set()

    for fpath in chunk_files:
        filename = fpath.name.lower()
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        if filename.startswith("constitution"):
            match = re.search(r'constitution_article_([0-9a-z]+)_chunk', filename)
            if match:
                constitution_articles.add(match.group(1).upper())
        elif filename.startswith("ppc"):
            match = re.search(r'ppc_section_([0-9a-z]+)_chunk', filename)
            if match:
                ppc_sections.add(match.group(1).upper())
        elif filename.startswith("crpc"):
            sec_match = re.search(r'(?:SECTION(?:/ARTICLE)?|ARTICLE):\s*(\d+[a-zA-Z]?)', text, re.IGNORECASE)
            if sec_match:
                crpc_sections.add(sec_match.group(1).upper())

    print("\n" + "="*60)
    print("KNOWLEDGE BASE COMPLETENESS AUDIT REPORT")
    print("="*60)

    # 1. Constitution Audit (Articles 8 to 28 + 9A/10A/19A/25A)
    expected_const = {str(i) for i in range(8, 29)} | {"9A", "10A", "19A", "25A"}
    missing_const = expected_const - constitution_articles
    print(f"\n[1] Constitution of Pakistan (Fundamental Rights 8 to 28):")
    print(f"    - Present in Vector Store: {len(constitution_articles & expected_const)} / {len(expected_const)} articles")
    if missing_const:
        print(f"    [!] Missing Articles: {sorted(list(missing_const))}")
    else:
        print("    [OK] 100% Complete! All Fundamental Rights Articles (8 to 28) are present.")

    # 2. Key PPC Sections Audit
    key_ppc_sections = {
        "109", "114", "120A", "120B", "141", "143", "147", "148", "149",
        "279", "299", "300", "302", "304", "316", "319", "320", "322",
        "324", "332", "337", "337A", "337B", "337C", "337D", "337E", "337F", "337G",
        "340", "341", "342", "354", "354A", "359", "360", "361", "362", "363", "364", "365", "365A",
        "375", "376", "378", "379", "380", "381", "382", "383", "384", "390", "391", "392", "393", "394", "395",
        "403", "405", "406", "411", "415", "420", "425", "426", "463", "464", "465", "496B", "497", "499", "500", "503", "506", "511"
    }
    missing_ppc = key_ppc_sections - ppc_sections
    print(f"\n[2] Pakistan Penal Code (PPC) - Core Criminal Offences:")
    print(f"    - Present in Vector Store: {len(ppc_sections & key_ppc_sections)} / {len(key_ppc_sections)} key sections")
    if missing_ppc:
        print(f"    [!] Missing Key PPC Sections: {sorted(list(missing_ppc))}")
    else:
        print("    [OK] 100% Complete! All major criminal offence sections present.")

    # 3. Key CrPC Sections Audit
    key_crpc_sections = {
        "54", "55", "59", "60", "61", "62", "87", "88", "96", "97", "100", "103",
        "154", "155", "156", "157", "161", "162", "164", "165", "167", "173", "174",
        "496", "497", "498", "498A", "499", "517", "561A"
    }
    missing_crpc = key_crpc_sections - crpc_sections
    print(f"\n[3] Code of Criminal Procedure (CrPC) - Core Procedure:")
    print(f"    - Present in Vector Store: {len(crpc_sections & key_crpc_sections)} / {len(key_crpc_sections)} key sections")
    if missing_crpc:
        print(f"    [!] Missing Key CrPC Sections: {sorted(list(missing_crpc))}")
    else:
        print("    [OK] 100% Complete! All core procedure & bail sections present.")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
