"""
Phase 3: Scrape Putusan Mahkamah Agung (putusan3.mahkamahagung.go.id)
Pattern dari: github.com/suryast/indonesia-gov-apis/apis/tier1-open-apis/putusan-ma
Key: POST ke /search/index/pencarian/ajax/putusan, header X-Requested-With
"""
from __future__ import annotations
import requests
import pandas as pd
import time
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://putusan3.mahkamahagung.go.id"

# Search queries relevan LEUI
SEARCHES = [
    # H1: Inconsistency risk - kasus perdata bisnis
    {"q": "wanprestasi kontrak", "label": "wanprestasi_kontrak"},
    {"q": "wanprestasi investasi", "label": "wanprestasi_investasi"},
    # H3: Procedural delay - sengketa perizinan
    {"q": "perizinan usaha", "label": "perizinan_usaha"},
    {"q": "sengketa perizinan", "label": "sengketa_perizinan"},
    # H4: Regulatory reversal - TUN
    {"q": "pencabutan izin", "label": "pencabutan_izin"},
    {"q": "tata usaha negara izin", "label": "tun_izin"},
    # H5: Criminal enforcement - pidana bisnis
    {"q": "penipuan investasi", "label": "penipuan_investasi"},
    {"q": "penggelapan perusahaan", "label": "penggelapan_perusahaan"},
]

# Tahun yang relevan (fokus 2015-2025 untuk tren terkini)
YEARS = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]


def search_ma(query, tahun, page=1):
    """Search Putusan MA via AJAX POST endpoint - per repo pattern."""
    try:
        resp = requests.post(
            f"{BASE}/search/index/pencarian/ajax/putusan",
            json={
                "q": query,
                "tahun": tahun,
                "jenis_doc": "Putusan",
                "page": page,
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=30,
            verify=False,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    except requests.RequestException as e:
        print(f"[ERROR] {e}")
        return None


def main():
    print("=" * 60)
    print("PHASE 3: Scraping Putusan MA (mahkamahagung.go.id)")
    print("Pattern: github.com/suryast/indonesia-gov-apis")
    print("=" * 60)

    all_records = []
    max_pages = 3  # Limit per query/year combo untuk sample

    for search in SEARCHES:
        query = search["q"]
        label = search["label"]

        for tahun in YEARS:
            print(f"\n[SEARCH] '{query}' | {tahun}...", end=" ", flush=True)

            for page in range(1, max_pages + 1):
                data = search_ma(query, tahun, page)

                if data is None:
                    print(f"[ERROR]", end=" ")
                    break

                decisions = data.get("data", [])
                if not decisions:
                    if page == 1:
                        print(f"0 results", end=" ")
                    break

                if page == 1:
                    total = data.get("total", len(decisions))
                    print(f"{total} total", end=" ", flush=True)

                for d in decisions:
                    record = {
                        "nomor": d.get("nomor", ""),
                        "tanggal_musyawarah": d.get("tanggal_musyawarah", ""),
                        "tanggal_registrasi": d.get("tanggal_registrasi", ""),
                        "pengadilan": d.get("pengadilan", ""),
                        "jenis_perkara": d.get("jenis_perkara", d.get("klasifikasi", "")),
                        "tahun_search": tahun,
                        "query_label": label,
                        "query": query,
                    }
                    # Extract any additional fields
                    for key in ["amar", "status", "klasifikasi", "sub_klasifikasi",
                                "lembaga_peradilan", "provinsi"]:
                        if key in d:
                            record[key] = d[key]
                    all_records.append(record)

                time.sleep(1)  # Rate limiting per repo recommendation

            time.sleep(0.5)

    if not all_records:
        print("\n\n[ERROR] No data scraped from MA!")
        # Debug: try a simple test query
        print("[DEBUG] Testing basic connectivity...")
        test = search_ma("putusan", "2024", 1)
        if test:
            print(f"  Test query worked! Keys: {list(test.keys())}")
            print(f"  Sample: {json.dumps(test, indent=2, default=str)[:500]}")
        else:
            print("  Test query also failed. Server may be down.")
        return

    df = pd.DataFrame(all_records)
    before = len(df)
    df = df.drop_duplicates(subset=["nomor"])
    print(f"\n\n[DEDUP] {before} -> {len(df)} unique decisions")

    # Save
    output_dir = os.path.join(os.path.dirname(__file__), "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "putusan_ma_sample.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SAVED] {output_path}")

    # Summary
    if "query_label" in df.columns:
        print("\n[CATEGORY] Per kategori pencarian:")
        for label, count in df["query_label"].value_counts().items():
            print(f"  {label}: {count}")

    if "tahun_search" in df.columns:
        print("\n[YEAR] Per tahun:")
        for y, c in df["tahun_search"].value_counts().sort_index().items():
            print(f"  {y}: {c}")

    if "jenis_perkara" in df.columns:
        print("\n[TYPE] Per jenis perkara:")
        for j, c in df["jenis_perkara"].value_counts().head(10).items():
            print(f"  {j}: {c}")

    # Durasi perkara (jika ada tanggal registrasi dan musyawarah)
    if "tanggal_registrasi" in df.columns and "tanggal_musyawarah" in df.columns:
        try:
            df["tgl_reg"] = pd.to_datetime(df["tanggal_registrasi"], errors="coerce")
            df["tgl_mus"] = pd.to_datetime(df["tanggal_musyawarah"], errors="coerce")
            df["durasi_hari"] = (df["tgl_mus"] - df["tgl_reg"]).dt.days
            valid_dur = df[df["durasi_hari"] > 0]["durasi_hari"]
            if not valid_dur.empty:
                print(f"\n[DURASI] Rata-rata durasi perkara: {valid_dur.mean():.0f} hari")
                print(f"  Median: {valid_dur.median():.0f} hari")
                print(f"  Min: {valid_dur.min()} | Max: {valid_dur.max()}")
        except Exception:
            pass

    print("\n[DONE] Phase 3 complete!")


if __name__ == "__main__":
    main()
