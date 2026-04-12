"""
Phase 1: Scrape JDIH BPK (peraturan.bpk.go.id)
Target: UU, PP, Perpres terkait investasi, perizinan, penanaman modal
Output: data/processed/regulasi_investasi_bisnis.csv
"""
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
import sys

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "https://peraturan.bpk.go.id"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Keywords terkait bisnis & investasi yang relevan untuk LEUI
KEYWORDS = [
    "penanaman modal",
    "perizinan berusaha", 
    "cipta kerja",
    "minerba",
    "pertambangan mineral",
    "ketenagakerjaan",
    "perseroan terbatas",
    "kepailitan",
    "arbitrase",
]

# Filter jenis peraturan yang paling relevan
JENIS_FILTER = ["UU", "PP", "Perpres", "Perppu"]


def scrape_search_page(keyword: str, page: int = 1, per_page: int = 10) -> list[dict]:
    """Scrape satu halaman hasil pencarian BPK JDIH."""
    results = []
    
    try:
        resp = requests.get(
            f"{BASE_URL}/Search",
            params={"query": keyword, "PerPage": per_page, "PageNum": 1, "p": page},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] Request failed for '{keyword}' page {page}: {e}")
        return results
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Cari semua link peraturan (pattern: /Details/{id}/{slug})
    detail_links = soup.find_all("a", href=re.compile(r"/Details/\d+/"))
    
    seen_ids = set()
    for link in detail_links:
        href = link.get("href", "")
        match = re.search(r"/Details/(\d+)/([\w-]+)", href)
        if not match:
            continue

        detail_id = match.group(1)
        slug = match.group(2)
        
        if detail_id in seen_ids:
            continue
        seen_ids.add(detail_id)
        
        title_text = link.get_text(strip=True)
        if not title_text or len(title_text) < 5:
            continue
            
        # Parse jenis dan nomor/tahun dari slug (e.g. "uu-no-6-tahun-2023")
        jenis = ""
        nomor = ""
        tahun = ""
        
        slug_upper = slug.upper().replace("-", " ")
        for j in JENIS_FILTER:
            if slug_upper.startswith(j.upper().replace("-", " ")):
                jenis = j
                break
        
        tahun_match = re.search(r"tahun[- ](\d{4})", slug, re.IGNORECASE)
        if tahun_match:
            tahun = tahun_match.group(1)
            
        nomor_match = re.search(r"no[- ]+(\d+)", slug, re.IGNORECASE)
        if nomor_match:
            nomor = nomor_match.group(1)
        
        results.append({
            "detail_id": detail_id,
            "slug": slug,
            "judul": title_text,
            "jenis": jenis,
            "nomor": nomor,
            "tahun": tahun,
            "keyword_search": keyword,
            "url": f"{BASE_URL}{href}" if not href.startswith("http") else href,
        })
    
    return results


def scrape_all_keywords(max_pages_per_keyword: int = 5) -> pd.DataFrame:
    """Scrape semua keyword, beberapa halaman per keyword."""
    all_results = []
    
    for keyword in KEYWORDS:
        print(f"\n[SEARCH] Searching: '{keyword}'")
        for page in range(1, max_pages_per_keyword + 1):
            print(f"  Page {page}...", end=" ", flush=True)
            results = scrape_search_page(keyword, page=page)
            print(f"found {len(results)} regulations")
            
            if not results:
                break
                
            all_results.extend(results)
            time.sleep(1)  # Rate limiting - 1 detik per request
    
    df = pd.DataFrame(all_results)
    
    if df.empty:
        print("\n[WARN] No results found!")
        return df, df
    
    # Deduplicate by detail_id
    before = len(df)
    df = df.drop_duplicates(subset=["detail_id"])
    print(f"\n[TOTAL] {before} results -> {len(df)} unique regulations")
    
    # Filter hanya UU, PP, Perpres, Perppu
    if not df.empty:
        df_filtered = df[df["jenis"].isin(JENIS_FILTER)]
        print(f"[FILTER] After filtering {JENIS_FILTER}: {len(df_filtered)} regulations")
        
        # Tapi simpan juga yang tidak terfilter untuk referensi
        return df, df_filtered
    
    return df, df


def main():
    print("=" * 60)
    print("PHASE 1: Scraping JDIH BPK - Regulasi Bisnis & Investasi")
    print("=" * 60)
    
    df_all, df_filtered = scrape_all_keywords(max_pages_per_keyword=3)
    
    if df_all.empty:
        print("[ERROR] No data scraped!")
        return
    
    # Save full results
    output_dir = os.path.join(os.path.dirname(__file__), "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    full_path = os.path.join(output_dir, "regulasi_investasi_bisnis_full.csv")
    df_all.to_csv(full_path, index=False, encoding="utf-8-sig")
    print(f"\n[SAVED] Full results saved: {full_path}")
    
    # Save filtered (UU/PP/Perpres only)
    filtered_path = os.path.join(output_dir, "regulasi_investasi_bisnis.csv")
    df_filtered.to_csv(filtered_path, index=False, encoding="utf-8-sig")
    print(f"[SAVED] Filtered results saved: {filtered_path}")
    
    # Summary per tahun
    if not df_filtered.empty and "tahun" in df_filtered.columns:
        print("\n[YEAR] Distribusi per Tahun (filtered):")
        tahun_counts = df_filtered[df_filtered["tahun"] != ""]["tahun"].value_counts().sort_index()
        for tahun, count in tahun_counts.items():
            print(f"  {tahun}: {count} regulasi")
    
    # Summary per jenis
    if not df_filtered.empty:
        print("\n[TYPE] Distribusi per Jenis:")
        jenis_counts = df_filtered["jenis"].value_counts()
        for jenis, count in jenis_counts.items():
            if jenis:
                print(f"  {jenis}: {count}")
    
    print("\n[DONE] Phase 1 complete!")


if __name__ == "__main__":
    main()
