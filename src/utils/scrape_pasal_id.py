"""
Phase 1B: Scrape Pasal.id REST API
Target: UU, PP, Perpres terkait investasi/bisnis + status (berlaku/dicabut/diubah)
Output: data/processed/regulasi_pasal_id.csv
"""
from __future__ import annotations
import requests
import pandas as pd
import time
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "https://pasal.id/api/v1"
TOKEN = "pasal_mcp_e2ae8b6e539d_f59d16d0b5fbbfa436ef11c17e0586f0adf6addafce6452f"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Jenis peraturan yang relevan untuk LEUI
TYPES = ["UU", "PERPPU", "PP", "PERPRES"]

# Tahun yang relevan (2003-2026 = era reformasi hukum bisnis)
YEARS = list(range(2003, 2027))


def fetch_laws_by_type_year(law_type, year, limit=50, offset=0):
    """Fetch daftar peraturan berdasarkan jenis dan tahun."""
    try:
        resp = requests.get(
            f"{BASE_URL}/laws",
            params={"type": law_type, "year": year, "limit": limit, "offset": offset},
            headers=HEADERS,
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            print(f"  [RATE LIMIT] Waiting 10s...")
            time.sleep(10)
            return fetch_laws_by_type_year(law_type, year, limit, offset)
        else:
            print(f"  [ERROR] {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.RequestException as e:
        print(f"  [ERROR] Request failed: {e}")
        return None


def search_laws(query, law_type=None, limit=20):
    """Search peraturan berdasarkan keyword."""
    params = {"q": query, "limit": limit}
    if law_type:
        params["type"] = law_type
    
    try:
        resp = requests.get(
            f"{BASE_URL}/search",
            params=params,
            headers=HEADERS,
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            print(f"  [RATE LIMIT] Waiting 10s...")
            time.sleep(10)
            return search_laws(query, law_type, limit)
        else:
            print(f"  [ERROR] {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.RequestException as e:
        print(f"  [ERROR] Request failed: {e}")
        return None


def main():
    print("=" * 60)
    print("PHASE 1B: Scraping Pasal.id REST API")
    print("=" * 60)
    
    all_laws = []
    
    # Strategy 1: Fetch all UU per year (2003-2026)
    print("\n--- Strategy 1: Fetch UU per tahun ---")
    for year in YEARS:
        print(f"  UU {year}...", end=" ", flush=True)
        data = fetch_laws_by_type_year("UU", year, limit=100)
        if data and "laws" in data:
            laws = data["laws"]
            print(f"found {len(laws)} (total in DB: {data.get('total', '?')})")
            for law in laws:
                law["source"] = "list_by_year"
            all_laws.extend(laws)
        else:
            print("no data")
        time.sleep(0.5)
    
    # Strategy 2: Search by keywords for more targeted results
    print("\n--- Strategy 2: Search by keyword ---")
    keywords = [
        "investasi",
        "penanaman modal",
        "perizinan",
        "cipta kerja",
        "minerba",
        "pertambangan",
        "ketenagakerjaan",
        "perseroan terbatas",
        "kepailitan",
        "arbitrase",
        "pencabutan izin",
        "tata usaha negara",
    ]
    
    for kw in keywords:
        print(f"  Search: '{kw}'...", end=" ", flush=True)
        data = search_laws(kw, limit=20)
        if data and "results" in data:
            results = data["results"]
            print(f"found {len(results)} (total: {data.get('total', '?')})")
            for r in results:
                work = r.get("work", {})
                work["source"] = f"search:{kw}"
                work["search_score"] = r.get("score", 0)
                work["snippet"] = r.get("snippet", "")
                all_laws.append(work)
        else:
            print("no data")
        time.sleep(0.5)
    
    if not all_laws:
        print("[ERROR] No data fetched!")
        return
    
    # Build DataFrame
    df = pd.DataFrame(all_laws)
    print(f"\n[RAW] Total records: {len(df)}")
    
    # Deduplicate by frbr_uri (unique identifier)
    if "frbr_uri" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["frbr_uri"])
        print(f"[DEDUP] {before} -> {len(df)} unique laws")
    
    # Save
    output_dir = os.path.join(os.path.dirname(__file__), "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "regulasi_pasal_id.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[SAVED] {output_path}")
    
    # Summary
    if "status" in df.columns:
        print("\n[STATUS] Distribusi status:")
        for status, count in df["status"].value_counts().items():
            print(f"  {status}: {count}")
    
    if "year" in df.columns:
        print("\n[YEAR] Distribusi per tahun:")
        year_counts = df["year"].value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"  {year}: {count}")
    
    if "type" in df.columns:
        print("\n[TYPE] Distribusi per jenis:")
        for t, count in df["type"].value_counts().items():
            print(f"  {t}: {count}")
    
    # Count status changes (dicabut/diubah) - key metric for LEUI
    if "status" in df.columns:
        changed = df[df["status"].isin(["dicabut", "diubah"])]
        print(f"\n[LEUI KEY METRIC] Regulasi dicabut/diubah: {len(changed)} dari {len(df)} ({len(changed)*100//len(df)}%)")
        if not changed.empty and "year" in changed.columns:
            print("  Per tahun:")
            for year, count in changed["year"].value_counts().sort_index().items():
                print(f"    {year}: {count} dicabut/diubah")
    
    print("\n[DONE] Phase 1B complete!")


if __name__ == "__main__":
    main()
