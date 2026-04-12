"""
Phase 2: Scrape Putusan Mahkamah Konstitusi (mkri.id)
Pattern dari: github.com/suryast/indonesia-gov-apis/apis/tier2-scrapeable/putusan-mk
Key: Harus pakai requests.Session() dan selector table.table tbody tr
"""
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Session-based approach per repo docs
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

KEYWORDS = [
    "cipta kerja",
    "investasi",
    "penanaman modal",
    "minerba",
    "pertambangan",
    "ketenagakerjaan",
    "perseroan",
    "perizinan",
    "BUMN",
    "perdagangan",
    "keuangan negara",
    "pajak",
]


def scrape_mk_search(keyword, page=1):
    """Scrape halaman pencarian Putusan MK - pakai Session per repo pattern."""
    results = []

    try:
        # Pattern langsung dari repo: session.get dengan params
        resp = session.get("https://mkri.id/index.php", params={
            "page": "web.Putusan",
            "id": "",
            "kat": "1",       # 1 = Putusan
            "cari": keyword,
            "hlm": page,
        }, timeout=30)

        if resp.status_code != 200:
            print(f"[HTTP {resp.status_code}]", end=" ")
            return results

    except requests.RequestException as e:
        print(f"[ERROR: {e}]", end=" ")
        return results

    soup = BeautifulSoup(resp.text, "html.parser")

    # Exact selector from repo: table.table tbody tr
    for row in soup.select("table.table tbody tr"):
        cells = row.find_all("td")
        if len(cells) >= 3:
            nomor = cells[0].get_text(strip=True)
            perihal = cells[1].get_text(strip=True)
            tanggal = cells[2].get_text(strip=True)
            amar = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            if not nomor or nomor.lower() in ["no", "nomor", "no."]:
                continue

            # Parse tahun dari nomor (e.g. "003/PUU-IV/2006")
            tahun_match = re.search(r"/(\d{4})$", nomor)
            tahun = tahun_match.group(1) if tahun_match else ""

            # Parse jenis perkara
            jenis = ""
            if "PUU" in nomor.upper():
                jenis = "PUU"
            elif "SKLN" in nomor.upper():
                jenis = "SKLN"
            elif "PHPU" in nomor.upper():
                jenis = "PHPU"

            results.append({
                "nomor": nomor,
                "perihal": perihal,
                "tanggal": tanggal,
                "amar": amar,
                "tahun": tahun,
                "jenis_perkara": jenis,
                "keyword_search": keyword,
            })

    # Fallback: jika selector table.table tidak match, coba semua tables
    if not results:
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 3:
                    nomor = cells[0].get_text(strip=True)
                    perihal = cells[1].get_text(strip=True)
                    tanggal = cells[2].get_text(strip=True)

                    if not nomor or len(nomor) < 3:
                        continue
                    if nomor.lower() in ["no", "nomor", "no."]:
                        continue

                    tahun_match = re.search(r"/(\d{4})$", nomor)
                    tahun = tahun_match.group(1) if tahun_match else ""

                    jenis = ""
                    if "PUU" in nomor.upper():
                        jenis = "PUU"

                    results.append({
                        "nomor": nomor,
                        "perihal": perihal,
                        "tanggal": tanggal,
                        "amar": "",
                        "tahun": tahun,
                        "jenis_perkara": jenis,
                        "keyword_search": keyword,
                    })

    return results


def main():
    print("=" * 60)
    print("PHASE 2: Scraping Putusan MK (mkri.id)")
    print("Pattern: github.com/suryast/indonesia-gov-apis")
    print("=" * 60)

    # First: warm up session by visiting the main page
    print("\n[INIT] Warming up session...")
    try:
        warm = session.get("https://mkri.id/index.php?page=web.Putusan", timeout=15)
        print(f"  Main page: HTTP {warm.status_code}, {len(warm.text)} bytes")
    except Exception as e:
        print(f"  [WARN] Warmup failed: {e}")

    time.sleep(1)

    all_results = []

    for keyword in KEYWORDS:
        print(f"\n[SEARCH] '{keyword}'...", end=" ", flush=True)
        results = scrape_mk_search(keyword)
        print(f"found {len(results)}")
        all_results.extend(results)
        time.sleep(1.5)

    if not all_results:
        print("\n[WARN] No results via search. Trying browse all pages...")
        # Fallback: browse tanpa keyword (semua putusan)
        for page_num in range(1, 6):
            print(f"  Page {page_num}...", end=" ", flush=True)
            results = scrape_mk_search("", page=page_num)
            print(f"found {len(results)}")
            all_results.extend(results)
            time.sleep(1.5)

    if not all_results:
        print("[ERROR] Could not scrape any data from mkri.id")
        print("Site may be blocking. Saving debug HTML...")
        debug_resp = session.get("https://mkri.id/index.php?page=web.Putusan", timeout=15)
        debug_path = os.path.join(os.path.dirname(__file__), "processed", "debug_mkri.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(debug_resp.text)
        print(f"  Debug HTML saved to: {debug_path}")
        print(f"  HTTP status: {debug_resp.status_code}")
        print(f"  Page size: {len(debug_resp.text)} bytes")
        return

    df = pd.DataFrame(all_results)
    before = len(df)
    df = df.drop_duplicates(subset=["nomor"])
    print(f"\n[DEDUP] {before} -> {len(df)} unique decisions")

    output_dir = os.path.join(os.path.dirname(__file__), "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "putusan_mk.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SAVED] {output_path}")

    if "jenis_perkara" in df.columns:
        print("\n[TYPE] Jenis perkara:")
        for j, c in df["jenis_perkara"].value_counts().items():
            print(f"  {j if j else '(other)'}: {c}")

    if "tahun" in df.columns:
        valid = df[df["tahun"] != ""]
        if not valid.empty:
            print("\n[YEAR] Per tahun:")
            for y, c in valid["tahun"].value_counts().sort_index().items():
                print(f"  {y}: {c}")

    print("\n[SAMPLE] 5 putusan:")
    for _, r in df.head(5).iterrows():
        print(f"  {r['nomor']}: {r['perihal'][:70]}")

    print("\n[DONE] Phase 2 complete!")


if __name__ == "__main__":
    main()
