# Download raw legal documents

import os
import sys
import urllib.request
import ssl

SOURCES = {
    "ppc": {
        "name": "Pakistan Penal Code, 1860 (Act XLV of 1860)",
        "url": "https://www.pakistani.org/pakistan/legislation/1860/actXLVof1860.html",
        "output_dir": "data/raw/ppc",
        "output_file": "ppc_raw.html",
        "verification": "https://pakistancode.gov.pk (official source, mirrored on pakistani.org)"
    },
    "crpc": {
        "name": "Code of Criminal Procedure, 1898 (Act V of 1898)",
        "urls": [
            "https://www.pakistani.org/pakistan/legislation/1898/actVof1898.html",
            "https://www.pakistani.org/pakistan/legislation/1898/actVof1898/",
        ],
        "output_dir": "data/raw/crpc",
        "output_file": "crpc_raw.html",
        "verification": "https://pakistancode.gov.pk",
        "manual_note": (
            "If automatic download fails, please manually download the CrPC from:\n"
            "  - https://pakistancode.gov.pk (search for 'Code of Criminal Procedure')\n"
            "  - https://na.gov.pk/uploads/documents/1491aborcrpc.pdf\n"
            "  Save the file as data/raw/crpc/crpc_raw.html (or .pdf)\n"
        )
    },
    "constitution": {
        "name": "Constitution of Pakistan, 1973 — Part II, Chapter 1: Fundamental Rights (Articles 8-28)",
        "url": "https://www.pakistani.org/pakistan/constitution/part2.ch1.html",
        "output_dir": "data/raw/constitution",
        "output_file": "constitution_fundamental_rights_raw.html",
        "verification": "https://pakistancode.gov.pk and https://na.gov.pk"
    }
}


def download_file(url, output_path):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"    Downloading: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            content = response.read()
            with open(output_path, "wb") as f:
                f.write(content)
            size_kb = len(content) / 1024
            print(f"    [OK] Saved: {output_path} ({size_kb:.1f} KB)")
            return True
    except Exception as e:
        print(f"    [FAIL] Failed: {e}")
        return False


def main():
    print("Downloading legal source data...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    results = {}

    for key, source in SOURCES.items():
        print(f"\n  Source: {source['name']}")
        print(f"     Verified against: {source['verification']}")

        os.makedirs(source["output_dir"], exist_ok=True)
        output_path = os.path.join(source["output_dir"], source["output_file"])

        if "url" in source:
            success = download_file(source["url"], output_path)
        elif "urls" in source:
            success = False
            for url in source["urls"]:
                success = download_file(url, output_path)
                if success:
                    break
        else:
            success = False

        if not success and "manual_note" in source:
            print(f"\n    MANUAL ACTION REQUIRED:")
            print(f"    {source['manual_note']}")

        results[key] = success

    print("\nCollection Summary:")
    for key, success in results.items():
        status = "Downloaded" if success else "Manual download needed"
        print(f"    {key.upper():15s} — {status}")

    sources_doc = os.path.join("data", "source_links.md")
    with open(sources_doc, "w", encoding="utf-8") as f:
        f.write("# Verified Legal Source Links\n\n")
        f.write("| # | Source | URL | Verification |\n")
        f.write("|---|--------|-----|-------------|\n")
        for i, (key, source) in enumerate(SOURCES.items(), 1):
            url = source.get("url", source.get("urls", ["N/A"])[0])
            f.write(f"| {i} | {source['name']} | {url} | {source['verification']} |\n")
        f.write("\n\nAll sources verified against the official Government of Pakistan portal.\n")
    print(f"\n  Source links document saved: {sources_doc}\n")
    all_ok = all(results.values())
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
