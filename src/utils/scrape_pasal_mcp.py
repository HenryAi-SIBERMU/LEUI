"""
Aksi 3: Enrichment pasal.id — Maximum data extraction & cleaning
Strategi:
  A. Search via pasal.id MCP Server REST (topik-topik LEUI)
  B. Cek get_law_status untuk UU kunci bisnis
  C. Merge dengan data existing (regulasi_pasal_id_raw.csv)
  D. Clean & categorize per hipotesis H1-H5
  E. Output CSV bersih untuk dashboard
"""
import requests
import pandas as pd
import time
import os
import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MCP_BASE = "https://pasal-mcp-server-production.up.railway.app"
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
os.makedirs(DATA_DIR, exist_ok=True)

# ================================================================
# TAXONOMY: Keyword → Hipotesis mapping (sesuai narasi LEUI)
# ================================================================
LEUI_SEARCH_TAXONOMY = {
    # H1: Inconsistency — regulasi yang menimbulkan multi-interpretasi
    "H1_inconsistency": [
        "penanaman modal", "investasi asing", "perseroan terbatas",
        "persaingan usaha", "antimonopoli",
    ],
    # H2: Selective Enforcement — regulasi korupsi, KPK, penegakan
    "H2_selective": [
        "pemberantasan korupsi", "tindak pidana korupsi",
        "pencucian uang", "suap",
    ],
    # H3: Procedural Uncertainty — perizinan, birokrasi, OSS
    "H3_procedural": [
        "perizinan berusaha", "cipta kerja", "online single submission",
        "izin usaha", "kemudahan berusaha",
    ],
    # H4: Regulatory Reversal — perubahan/pencabutan UU
    "H4_reversal": [
        "pertambangan mineral", "kehutanan", "perkebunan",
        "ketenagakerjaan", "pajak penghasilan",
        "pajak pertambahan nilai",
    ],
    # H5: Criminalization — pidana korporasi, pemidanaan bisnis
    "H5_criminalization": [
        "tindak pidana korporasi", "kepailitan",
        "penundaan kewajiban pembayaran utang", "pengadilan niaga",
        "pasar modal",
    ],
}

# UU Kunci yang PASTI dibutuhkan status reversal-nya
KEY_LAWS = [
    # Investasi & Bisnis Core
    {"id": "uu-25-2007", "nama": "UU 25/2007 Penanaman Modal", "hipotesis": "H1"},
    {"id": "uu-40-2007", "nama": "UU 40/2007 Perseroan Terbatas", "hipotesis": "H1"},
    {"id": "uu-5-1999", "nama": "UU 5/1999 Larangan Monopoli", "hipotesis": "H1"},
    # Korupsi & Enforcement
    {"id": "uu-31-1999", "nama": "UU 31/1999 Pemberantasan Tipikor", "hipotesis": "H2"},
    {"id": "uu-20-2001", "nama": "UU 20/2001 Perubahan UU Tipikor", "hipotesis": "H2"},
    {"id": "uu-30-2002", "nama": "UU 30/2002 KPK", "hipotesis": "H2"},
    {"id": "uu-19-2019", "nama": "UU 19/2019 Perubahan UU KPK", "hipotesis": "H2"},
    # Perizinan & Cipta Kerja
    {"id": "uu-11-2020", "nama": "UU 11/2020 Cipta Kerja", "hipotesis": "H3"},
    {"id": "uu-6-2023", "nama": "UU 6/2023 Penetapan Perpu Cipta Kerja", "hipotesis": "H3"},
    # Sektoral — target reversal
    {"id": "uu-4-2009", "nama": "UU 4/2009 Minerba", "hipotesis": "H4"},
    {"id": "uu-3-2020", "nama": "UU 3/2020 Perubahan UU Minerba", "hipotesis": "H4"},
    {"id": "uu-13-2003", "nama": "UU 13/2003 Ketenagakerjaan", "hipotesis": "H4"},
    {"id": "uu-32-2009", "nama": "UU 32/2009 Perlindungan Lingkungan", "hipotesis": "H4"},
    {"id": "uu-41-1999", "nama": "UU 41/1999 Kehutanan", "hipotesis": "H4"},
    {"id": "uu-36-2008", "nama": "UU 36/2008 Pajak Penghasilan", "hipotesis": "H4"},
    {"id": "uu-42-2009", "nama": "UU 42/2009 PPN", "hipotesis": "H4"},
    {"id": "uu-7-2021", "nama": "UU 7/2021 Harmonisasi Peraturan Perpajakan", "hipotesis": "H4"},
    # Kepailitan & Pidana Korporasi
    {"id": "uu-37-2004", "nama": "UU 37/2004 Kepailitan & PKPU", "hipotesis": "H5"},
    {"id": "uu-8-1995", "nama": "UU 8/1995 Pasar Modal", "hipotesis": "H5"},
]


def safe_mcp_post(endpoint, payload, timeout=20, max_retries=3):
    """POST ke MCP server dengan retry logic (Railway cold start)."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(f"{MCP_BASE}{endpoint}", json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return {"error": "endpoint_not_found"}
            elif resp.status_code == 500:
                return {"error": "server_error", "detail": resp.text[:200]}
            else:
                return {"error": f"http_{resp.status_code}"}
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"[timeout, retry {attempt+2}]", end=" ", flush=True)
                time.sleep(3 * (attempt + 1))
            else:
                return {"error": "timeout_final"}
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"[conn_err, retry {attempt+2}]", end=" ", flush=True)
                time.sleep(5)
            else:
                return {"error": "connection_failed"}
    return {"error": "max_retries"}


def phase_a_search_mcp():
    """Phase A: Search pasal.id MCP untuk setiap topik LEUI."""
    print("=" * 70)
    print("PHASE A: Search pasal.id MCP per topik LEUI")
    print("=" * 70)

    all_results = []

    for hipotesis, keywords in LEUI_SEARCH_TAXONOMY.items():
        print(f"\n--- {hipotesis} ---")
        for kw in keywords:
            print(f"  '{kw}'...", end=" ", flush=True)
            data = safe_mcp_post("/tools/search_laws", {"query": kw, "limit": 30})

            if "error" in data:
                print(f"[{data['error']}]")
                continue

            # MCP might return results in various formats
            results = data if isinstance(data, list) else data.get("results", data.get("data", []))
            if not isinstance(results, list):
                print(f"[unexpected format: {type(results)}]")
                continue

            print(f"[{len(results)} results]")
            for r in results:
                record = {
                    "hipotesis": hipotesis,
                    "search_query": kw,
                    "source": "mcp_search",
                }
                if isinstance(r, dict):
                    record.update({
                        "law_id": r.get("id", r.get("law_id", "")),
                        "title": r.get("title", r.get("judul", "")),
                        "type": r.get("type", r.get("jenis", "")),
                        "year": r.get("year", r.get("tahun", "")),
                        "number": r.get("number", r.get("nomor", "")),
                        "status": r.get("status", ""),
                        "frbr_uri": r.get("frbr_uri", r.get("uri", "")),
                    })
                all_results.append(record)

            time.sleep(1)

    df = pd.DataFrame(all_results)
    print(f"\nPhase A total: {len(df)} records from MCP search")
    return df


def phase_b_status_check():
    """Phase B: Cek get_law_status untuk UU kunci → reversal chain."""
    print("\n" + "=" * 70)
    print("PHASE B: get_law_status untuk 19 UU Kunci Bisnis")
    print("=" * 70)

    results = []

    for law in KEY_LAWS:
        print(f"  {law['id']} ({law['nama']})...", end=" ", flush=True)
        data = safe_mcp_post("/tools/get_law_status", {"law_id": law["id"]})

        if "error" in data:
            print(f"[{data['error']}]")
            results.append({
                "law_id": law["id"],
                "nama_uu": law["nama"],
                "hipotesis": law["hipotesis"],
                "status_api": "error",
                "amended_by": "",
                "revoked_by": "",
                "raw_response": str(data),
            })
        else:
            status = data.get("status", "unknown")
            amended_by = ", ".join(data.get("amended_by", [])) if isinstance(data.get("amended_by"), list) else str(data.get("amended_by", ""))
            revoked_by = ", ".join(data.get("revoked_by", [])) if isinstance(data.get("revoked_by"), list) else str(data.get("revoked_by", ""))
            replaces = ", ".join(data.get("replaces", [])) if isinstance(data.get("replaces"), list) else str(data.get("replaces", ""))

            marker = "✅" if status in ("berlaku", "active") else "🔴" if status in ("tidak_berlaku", "revoked") else "🟡"
            print(f"[{marker} {status}]", end="")
            if amended_by:
                print(f" diubah oleh: {amended_by}", end="")
            if revoked_by:
                print(f" dicabut oleh: {revoked_by}", end="")
            print()

            results.append({
                "law_id": law["id"],
                "nama_uu": law["nama"],
                "hipotesis": law["hipotesis"],
                "status_api": status,
                "amended_by": amended_by,
                "revoked_by": revoked_by,
                "replaces": replaces,
                "raw_response": str(data),
            })

        time.sleep(1)

    df = pd.DataFrame(results)
    print(f"\nPhase B total: {len(df)} UU kunci dicek")
    return df


def phase_c_merge_existing(df_mcp, df_status):
    """Phase C: Merge dengan data existing dari regulasi_pasal_id_raw.csv."""
    print("\n" + "=" * 70)
    print("PHASE C: Merge dengan data existing")
    print("=" * 70)

    existing_path = os.path.join(DATA_DIR, "regulasi_pasal_id_raw.csv")
    if os.path.exists(existing_path):
        df_existing = pd.read_csv(existing_path, encoding="utf-8-sig")
        print(f"  Existing data: {len(df_existing)} regulasi")
    else:
        df_existing = pd.DataFrame()
        print("  No existing data found")

    return df_existing


def phase_d_clean_categorize(df_existing, df_mcp, df_status):
    """Phase D: Clean & categorize semua data per hipotesis LEUI."""
    print("\n" + "=" * 70)
    print("PHASE D: Clean & Categorize per Hipotesis LEUI")
    print("=" * 70)

    # --- Cleaning existing 848 regulasi ---
    df = df_existing.copy() if len(df_existing) > 0 else pd.DataFrame()

    if len(df) > 0:
        # Remove HTML tags from snippet
        if "snippet" in df.columns:
            df["snippet"] = df["snippet"].astype(str).apply(
                lambda x: re.sub(r'<[^>]+>', '', x) if x != "nan" else ""
            )

        # Standardize status
        df["status"] = df["status"].str.lower().str.strip()
        df["status"] = df["status"].replace({
            "tidak berlaku": "tidak_berlaku",
            "revoked": "tidak_berlaku",
            "amended": "diubah",
        })

        # Extract year as int
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

        # Categorize by title keyword matching
        def assign_hipotesis(title):
            t = str(title).lower()
            cats = []
            # H1 — Inconsistency (investment/company/competition law)
            if any(k in t for k in ["penanaman modal", "investasi", "perseroan", "persaingan", "monopoli"]):
                cats.append("H1")
            # H2 — Selective enforcement (corruption, KPK)
            if any(k in t for k in ["korupsi", "kpk", "pencucian uang", "suap", "gratifikasi"]):
                cats.append("H2")
            # H3 — Procedural (licensing, permits, cipta kerja)
            if any(k in t for k in ["perizinan", "cipta kerja", "izin usaha", "oss", "kemudahan berusaha"]):
                cats.append("H3")
            # H4 — Reversal (sectoral laws that get changed frequently)
            if any(k in t for k in ["pertambangan", "kehutanan", "perkebunan", "ketenagakerjaan",
                                     "pajak", "cukai", "lingkungan hidup", "tata ruang",
                                     "mineral", "batu bara", "energi"]):
                cats.append("H4")
            # H5 — Criminalization (bankruptcy, capital markets, corporate crime)
            if any(k in t for k in ["kepailitan", "pkpu", "pasar modal", "pidana korporasi",
                                     "pengadilan niaga", "efek"]):
                cats.append("H5")
            return "; ".join(cats) if cats else "GENERAL"

        df["hipotesis"] = df["title"].apply(assign_hipotesis)

        # Filter: hanya yang relevan LEUI (bukan "GENERAL" = noise)
        df_leui = df[df["hipotesis"] != "GENERAL"].copy()
        df_general = df[df["hipotesis"] == "GENERAL"].copy()

        print(f"  Total existing: {len(df)}")
        print(f"  Relevan LEUI : {len(df_leui)}")
        print(f"  General/noise: {len(df_general)}")
    else:
        df_leui = pd.DataFrame()

    # --- Add MCP search results ---
    if len(df_mcp) > 0:
        df_mcp_clean = df_mcp.copy()
        if "title" in df_mcp_clean.columns:
            df_mcp_clean["title"] = df_mcp_clean["title"].str.strip()
        # Tag these as coming from MCP
        df_mcp_clean["data_source"] = "mcp_search_fresh"
        print(f"  MCP search data: {len(df_mcp_clean)} records added")
    else:
        df_mcp_clean = pd.DataFrame()

    # --- Compose final output ---
    # File 1: Cleaned & categorized full regulation list (LEUI-relevant only)
    if len(df_leui) > 0:
        out_cols = ["title", "type", "number", "year", "status", "hipotesis", "frbr_uri"]
        available = [c for c in out_cols if c in df_leui.columns]
        df_out1 = df_leui[available].copy()
        df_out1 = df_out1.sort_values(["hipotesis", "year"], ascending=[True, False])
        path1 = os.path.join(DATA_DIR, "regulasi_leui_cleaned.csv")
        df_out1.to_csv(path1, index=False, encoding="utf-8-sig")
        print(f"\n  [SAVED] {path1} ({len(df_out1)} rows)")

        # Print distribution
        print("\n  Distribusi per Hipotesis:")
        for h in ["H1", "H2", "H3", "H4", "H5"]:
            count = df_out1["hipotesis"].str.contains(h).sum()
            print(f"    {h}: {count} regulasi")

        print(f"\n  Distribusi Status (LEUI subset):")
        print(f"    {df_out1['status'].value_counts().to_dict()}")

    # File 2: Regulatory reversal timeline (H4 focus)
    if len(df_leui) > 0:
        df_reversal = df_leui[
            (df_leui["status"].isin(["tidak_berlaku", "diubah"])) |
            (df_leui["hipotesis"].str.contains("H4"))
        ].copy()
        if len(df_reversal) > 0:
            path2 = os.path.join(DATA_DIR, "h4_reversal_timeline.csv")
            df_reversal.to_csv(path2, index=False, encoding="utf-8-sig")
            print(f"\n  [SAVED] {path2} ({len(df_reversal)} rows — H4 reversal focus)")

    # File 3: Time-series regulatory churn rate per tahun
    if len(df) > 0 and "year" in df.columns:
        df_valid = df[df["year"].notna()].copy()
        yearly = df_valid.groupby("year").agg(
            total=("status", "count"),
            berlaku=("status", lambda x: (x == "berlaku").sum()),
            tidak_berlaku=("status", lambda x: (x == "tidak_berlaku").sum()),
            diubah=("status", lambda x: (x == "diubah").sum()),
        ).reset_index()
        yearly["churn_rate"] = ((yearly["tidak_berlaku"] + yearly["diubah"]) / yearly["total"] * 100).round(1)
        yearly = yearly.sort_values("year")

        path3 = os.path.join(DATA_DIR, "regulatory_churn_rate.csv")
        yearly.to_csv(path3, index=False, encoding="utf-8-sig")
        print(f"\n  [SAVED] {path3} ({len(yearly)} years — churn rate time series)")

        # Show key years
        print("\n  Regulatory Churn Rate (key years):")
        for _, row in yearly[yearly["year"] >= 2015].iterrows():
            bar = "█" * int(row["churn_rate"] / 2) if row["churn_rate"] > 0 else ""
            print(f"    {int(row['year'])}: {row['churn_rate']}% {bar} ({int(row['total'])} total)")

    # File 4: UU Status Chain (from Phase B)
    if len(df_status) > 0:
        path4 = os.path.join(DATA_DIR, "h4_uu_status_chain.csv")
        df_status.to_csv(path4, index=False, encoding="utf-8-sig")
        print(f"\n  [SAVED] {path4} ({len(df_status)} UU kunci — status chain dari MCP)")

    # File 5: MCP fresh search results
    if len(df_mcp_clean) > 0:
        path5 = os.path.join(DATA_DIR, "regulasi_mcp_fresh.csv")
        df_mcp_clean.to_csv(path5, index=False, encoding="utf-8-sig")
        print(f"\n  [SAVED] {path5} ({len(df_mcp_clean)} rows — fresh MCP search)")

    return df_leui


def main():
    print("=" * 70)
    print("AKSI 3: Enrichment pasal.id — FULL PIPELINE")
    print("=" * 70)

    # Phase A: Search MCP
    df_mcp = phase_a_search_mcp()

    # Phase B: Status check key laws
    df_status = phase_b_status_check()

    # Phase C: Load existing
    df_existing = phase_c_merge_existing(df_mcp, df_status)

    # Phase D: Clean & categorize
    df_final = phase_d_clean_categorize(df_existing, df_mcp, df_status)

    print("\n" + "=" * 70)
    print("AKSI 3 SELESAI!")
    print("=" * 70)
    print(f"\nOutput files di: {DATA_DIR}")
    print("  1. regulasi_leui_cleaned.csv    — Regulasi relevan LEUI per hipotesis")
    print("  2. h4_reversal_timeline.csv     — H4: Timeline regulasi dicabut/diubah")
    print("  3. regulatory_churn_rate.csv    — Time-series churn rate per tahun")
    print("  4. h4_uu_status_chain.csv       — Status chain 19 UU kunci dari MCP")
    print("  5. regulasi_mcp_fresh.csv       — Fresh data dari MCP search")


if __name__ == "__main__":
    main()
