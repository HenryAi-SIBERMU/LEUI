"""
FASE 0: Enrichment Script — Parse OSINT metadata menjadi time-series ready
Input: 3 CSV OSINT mentah (MA, MK, SIPP) + regulasi + SIPP existing
Output: 5 CSV enriched siap visualisasi dashboard
"""
import re
import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))

# ═══════════════════════════════════════════════════════
# 1. ENRICH PUTUSAN MA OSINT
# ═══════════════════════════════════════════════════════
def enrich_ma():
    print("=" * 60)
    print("1. ENRICHING PUTUSAN MA OSINT")
    print("=" * 60)
    
    path = os.path.join(DATA, "putusan_ma_osint.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"   Raw rows: {len(df)}")
    
    # --- Extract year from title/snippet/url ---
    def extract_year(row):
        text = f"{row.get('title','')} {row.get('snippet','')} {row.get('url','')}"
        # Try formal putusan number pattern first: Nomor XX/Pdt.G/YYYY
        m = re.search(r'/(\d{4})/', text)
        if m:
            yr = int(m.group(1))
            if 1990 <= yr <= 2026:
                return yr
        # Try 4-digit year in snippet
        years = re.findall(r'\b(20[0-2]\d|199\d)\b', text)
        if years:
            return int(max(years))  # take latest year mentioned
        return None
    
    # --- Extract jenis perkara from query/title/snippet ---
    def extract_jenis(row):
        text = f"{row.get('title','')} {row.get('snippet','')} {row.get('query','')}".lower()
        if 'wanprestasi' in text:
            return 'Wanprestasi'
        elif 'perizinan' in text or 'izin' in text:
            return 'Perizinan Usaha'
        elif 'pencabutan' in text or 'tambang' in text:
            return 'Pencabutan Izin Tambang'
        elif 'saham' in text or 'perseroan' in text:
            return 'Sengketa Perseroan'
        elif 'investasi' in text:
            return 'Sengketa Investasi'
        else:
            return 'Perdata Bisnis Lain'
    
    # --- Extract nomor putusan ---
    def extract_nomor(row):
        text = f"{row.get('title','')} {row.get('snippet','')}"
        # Pattern: Nomor 123/Pdt.G/2024/PN Xxx or similar
        m = re.search(r'(?:Nomor|No\.?)\s*(\d+/[A-Za-z\.]+/\d{4}(?:/[A-Z]+\s*[A-Za-z]*)?)', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # Simpler pattern: just XX/Pdt/YYYY
        m = re.search(r'(\d+/Pdt[^/]*/\d{4})', text, re.IGNORECASE)
        if m:
            return m.group(1)
        return ''
    
    df['year'] = df.apply(extract_year, axis=1)
    df['jenis_perkara'] = df.apply(extract_jenis, axis=1)
    df['nomor_putusan'] = df.apply(extract_nomor, axis=1)
    
    # Drop rows without year
    before = len(df)
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)
    print(f"   After year extraction: {len(df)} (dropped {before - len(df)} tanpa tahun)")
    
    # Aggregate time-series
    ts = df.groupby(['year', 'jenis_perkara']).size().reset_index(name='jumlah_putusan')
    ts_total = df.groupby('year').size().reset_index(name='total_putusan')
    
    # Save enriched detail
    out_detail = os.path.join(DATA, "putusan_ma_enriched.csv")
    df.to_csv(out_detail, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_detail}")
    
    # Save time-series
    out_ts = os.path.join(DATA, "putusan_ma_timeseries.csv")
    ts.to_csv(out_ts, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_ts}")
    
    # Save total per year
    out_total = os.path.join(DATA, "putusan_ma_yearly.csv")
    ts_total.to_csv(out_total, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_total}")
    
    print(f"\n   Breakdown per Jenis Perkara:")
    print(df['jenis_perkara'].value_counts().to_string())
    print(f"\n   Breakdown per Tahun:")
    print(ts_total.to_string())
    
    return df


# ═══════════════════════════════════════════════════════
# 2. ENRICH PUTUSAN MK OSINT
# ═══════════════════════════════════════════════════════
def enrich_mk():
    print("\n" + "=" * 60)
    print("2. ENRICHING PUTUSAN MK OSINT")
    print("=" * 60)
    
    path = os.path.join(DATA, "putusan_mk_osint.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"   Raw rows: {len(df)}")
    
    # --- Extract year from kandidat_nomor (e.g. 168/PUU-XXI/2023 → 2023) ---
    def extract_mk_year(row):
        nomor = str(row.get('kandidat_nomor', ''))
        # Direct year at end: /2023, /2024, /2025
        m = re.search(r'/(\d{4})$', nomor)
        if m:
            return int(m.group(1))
        # From title/snippet
        text = f"{row.get('title','')} {row.get('snippet','')}"
        years = re.findall(r'\b(20[0-2]\d)\b', text)
        if years:
            return int(max(years))
        return None
    
    # --- Extract UU yang diuji from snippet ---
    def extract_uu_diuji(row):
        text = f"{row.get('title','')} {row.get('snippet','')}"
        # Pattern: UU No/Nomor XX Tahun YYYY tentang XYZ
        m = re.search(r'(?:UU|Undang-Undang)\s*(?:No\.?|Nomor)\s*(\d+)\s*(?:Tahun)\s*(\d{4})\s*(?:tentang\s+)?([^,\.\;]{5,60})?', text, re.IGNORECASE)
        if m:
            uu_no = m.group(1)
            uu_yr = m.group(2)
            uu_ttg = (m.group(3) or '').strip()
            return f"UU {uu_no}/{uu_yr} {uu_ttg}".strip()
        # Simpler: Cipta Kerja
        if 'cipta kerja' in text.lower():
            return 'UU Cipta Kerja'
        if 'penanaman modal' in text.lower():
            return 'UU 25/2007 Penanaman Modal'
        if 'ketenagakerjaan' in text.lower():
            return 'UU 13/2003 Ketenagakerjaan'
        if 'minerba' in text.lower() or 'mineral' in text.lower():
            return 'UU Minerba'
        if 'kehutanan' in text.lower():
            return 'UU Kehutanan'
        return 'UU Lainnya'
    
    # --- Guess amar (dikabulkan/ditolak) from snippet ---
    def guess_amar(row):
        text = f"{row.get('snippet','')} {row.get('title','')}".lower()
        if any(k in text for k in ['dikabulkan', 'mengabulkan', 'inkonstitusional', 'bertentangan']):
            return 'Dikabulkan'
        elif any(k in text for k in ['ditolak', 'menolak', 'tidak dapat diterima']):
            return 'Ditolak'
        else:
            return 'Tidak Teridentifikasi'
    
    df['year'] = df.apply(extract_mk_year, axis=1)
    df['uu_diuji'] = df.apply(extract_uu_diuji, axis=1)
    df['amar'] = df.apply(guess_amar, axis=1)
    
    before = len(df)
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)
    print(f"   After year extraction: {len(df)} (dropped {before - len(df)})")
    
    # Time-series
    ts = df.groupby(['year', 'amar']).size().reset_index(name='jumlah')
    ts_total = df.groupby('year').size().reset_index(name='total_putusan_mk')
    
    # UU breakdown
    uu_breakdown = df.groupby(['uu_diuji', 'amar']).size().reset_index(name='jumlah')
    
    out_detail = os.path.join(DATA, "putusan_mk_enriched.csv")
    df.to_csv(out_detail, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_detail}")
    
    out_ts = os.path.join(DATA, "putusan_mk_timeseries.csv")
    ts.to_csv(out_ts, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_ts}")
    
    out_yearly = os.path.join(DATA, "putusan_mk_yearly.csv")
    ts_total.to_csv(out_yearly, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_yearly}")
    
    out_uu = os.path.join(DATA, "mk_uu_breakdown.csv")
    uu_breakdown.to_csv(out_uu, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_uu}")
    
    print(f"\n   Breakdown per Amar:")
    print(df['amar'].value_counts().to_string())
    print(f"\n   Breakdown per UU Diuji:")
    print(df['uu_diuji'].value_counts().to_string())
    print(f"\n   Breakdown per Tahun:")
    print(ts_total.to_string())
    
    return df


# ═══════════════════════════════════════════════════════
# 3. ENRICH SIPP OSINT + MERGE SIPP EXISTING
# ═══════════════════════════════════════════════════════
def enrich_sipp():
    print("\n" + "=" * 60)
    print("3. ENRICHING SIPP (OSINT + EXISTING)")
    print("=" * 60)

    # --- SIPP Existing (Sidoarjo + Negara) ---
    path_exist = os.path.join(DATA, "putusan_sipp_sidoarjo_negara_wanprestasi.csv")
    df_exist = pd.read_csv(path_exist, encoding="utf-8-sig")
    print(f"   SIPP Existing (Sidoarjo+Negara): {len(df_exist)} rows")
    
    # Parse Tanggal Register → year
    def parse_sipp_date(d):
        try:
            return pd.to_datetime(d, format='%d %b %Y').year
        except:
            try:
                return pd.to_datetime(d, dayfirst=True).year
            except:
                return None
    
    df_exist['year'] = df_exist['Tanggal Register'].apply(parse_sipp_date)
    df_exist['pengadilan'] = df_exist['Sumber PN']
    df_exist['jenis_perkara'] = 'Wanprestasi / PMH'
    df_exist['lama_proses'] = pd.to_numeric(df_exist['Lama Proses'], errors='coerce')
    df_exist['sumber'] = 'Direct Scrape'
    
    # --- SIPP OSINT ---
    path_osint = os.path.join(DATA, "sipp_nasional_osint.csv")
    df_osint = pd.read_csv(path_osint, encoding="utf-8-sig")
    print(f"   SIPP OSINT (Nasional): {len(df_osint)} rows")
    
    def extract_sipp_year(row):
        text = f"{row.get('title','')} {row.get('snippet','')}"
        years = re.findall(r'\b(202[0-6]|201\d)\b', text)
        if years:
            return int(max(years))
        return None
    
    def extract_sipp_jenis(row):
        text = f"{row.get('title','')} {row.get('snippet','')}".lower()
        if 'wanprestasi' in text:
            return 'Wanprestasi'
        elif 'perbuatan melawan hukum' in text or 'pmh' in text:
            return 'Perbuatan Melawan Hukum'
        elif 'gugatan' in text:
            return 'Gugatan Perdata'
        else:
            return 'Perdata Lain'
    
    # Extract nomor perkara from snippet
    def extract_sipp_nomor(row):
        text = f"{row.get('snippet','')}"
        m = re.search(r'(\d+/Pdt[^,\s]*(?:/\d{4})?(?:/PN\s*[A-Za-z]+)?)', text, re.IGNORECASE)
        if m:
            return m.group(1)
        return ''
    
    df_osint['year'] = df_osint.apply(extract_sipp_year, axis=1)
    df_osint['jenis_perkara'] = df_osint.apply(extract_sipp_jenis, axis=1)
    df_osint['nomor_perkara'] = df_osint.apply(extract_sipp_nomor, axis=1)
    df_osint['lama_proses'] = np.nan  # OSINT doesn't have this
    df_osint['sumber'] = 'OSINT Google CSE'
    
    # --- MERGE ---
    cols_unified = ['year', 'pengadilan', 'jenis_perkara', 'lama_proses', 'sumber']
    
    df_exist_clean = df_exist[cols_unified].copy()
    df_osint_clean = df_osint[cols_unified].copy()
    
    df_merged = pd.concat([df_exist_clean, df_osint_clean], ignore_index=True)
    df_merged = df_merged.dropna(subset=['year'])
    df_merged['year'] = df_merged['year'].astype(int)
    
    print(f"   Merged total: {len(df_merged)} perkara")
    
    # --- Stats ---
    durasi_stats = df_merged['lama_proses'].dropna()
    print(f"\n   Durasi Proses (dari {len(durasi_stats)} kasus dengan data durasi):")
    if len(durasi_stats) > 0:
        print(f"     Mean:   {durasi_stats.mean():.1f} hari")
        print(f"     Median: {durasi_stats.median():.1f} hari")
        print(f"     Max:    {durasi_stats.max():.0f} hari")
        print(f"     Min:    {durasi_stats.min():.0f} hari")
        print(f"     Std:    {durasi_stats.std():.1f} hari")
    
    # Distribution by PN
    pn_dist = df_merged.groupby('pengadilan').agg(
        jumlah=('year', 'size'),
        avg_durasi=('lama_proses', 'mean')
    ).sort_values('jumlah', ascending=False).reset_index()
    
    # Time-series
    ts = df_merged.groupby(['year', 'jenis_perkara']).size().reset_index(name='jumlah')
    ts_total = df_merged.groupby('year').size().reset_index(name='total_perkara')
    
    # Durasi distribution buckets
    if len(durasi_stats) > 0:
        bins = [0, 7, 30, 90, 180, 365, 9999]
        labels = ['< 1 minggu', '1-4 minggu', '1-3 bulan', '3-6 bulan', '6-12 bulan', '> 1 tahun']
        df_durasi = df_merged.dropna(subset=['lama_proses']).copy()
        df_durasi['durasi_bucket'] = pd.cut(df_durasi['lama_proses'], bins=bins, labels=labels, right=True)
        durasi_dist = df_durasi.groupby('durasi_bucket', observed=True).size().reset_index(name='jumlah')
    else:
        durasi_dist = pd.DataFrame()
    
    # Save
    out_merged = os.path.join(DATA, "sipp_merged_enriched.csv")
    df_merged.to_csv(out_merged, index=False, encoding="utf-8-sig")
    print(f"\n   [SAVED] {out_merged}")
    
    out_pn = os.path.join(DATA, "sipp_pn_distribution.csv")
    pn_dist.to_csv(out_pn, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_pn}")
    
    out_ts = os.path.join(DATA, "sipp_yearly.csv")
    ts_total.to_csv(out_ts, index=False, encoding="utf-8-sig")
    print(f"   [SAVED] {out_ts}")
    
    if len(durasi_dist) > 0:
        out_dur = os.path.join(DATA, "sipp_durasi_distribution.csv")
        durasi_dist.to_csv(out_dur, index=False, encoding="utf-8-sig")
        print(f"   [SAVED] {out_dur}")
    
    print(f"\n   Distribusi per Pengadilan Negeri (Top 10):")
    print(pn_dist.head(10).to_string())
    print(f"\n   Distribusi per Tahun:")
    print(ts_total.to_string())
    
    return df_merged


# ═══════════════════════════════════════════════════════
# 4. ENRICH REGULASI LEUI PER HIPOTESIS
# ═══════════════════════════════════════════════════════
def enrich_regulasi():
    print("\n" + "=" * 60)
    print("4. ENRICHING REGULASI LEUI PER HIPOTESIS")
    print("=" * 60)
    
    path = os.path.join(DATA, "regulasi_leui_cleaned.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"   Total regulasi: {len(df)}")
    
    # Per hipotesis breakdown
    for h in ['H1', 'H2', 'H3', 'H4', 'H5']:
        subset = df[df['hipotesis'] == h]
        if len(subset) == 0:
            print(f"   {h}: 0 regulasi")
            continue
            
        # Time-series per status
        ts = subset.groupby(['year', 'status']).size().reset_index(name='jumlah')
        ts_total = subset.groupby('year').size().reset_index(name='total')
        
        out = os.path.join(DATA, f"regulasi_{h.lower()}_yearly.csv")
        ts.to_csv(out, index=False, encoding="utf-8-sig")
        
        print(f"   {h}: {len(subset)} regulasi | berlaku={len(subset[subset['status']=='berlaku'])} | dicabut/diubah={len(subset[subset['status']!='berlaku'])}")
    
    # Summary table
    summary = df.groupby(['hipotesis', 'status']).size().reset_index(name='count')
    out_summary = os.path.join(DATA, "regulasi_summary_per_hipotesis.csv")
    summary.to_csv(out_summary, index=False, encoding="utf-8-sig")
    print(f"\n   [SAVED] {out_summary}")
    print(summary.to_string())
    
    return df


# ═══════════════════════════════════════════════════════
# 5. BUILD H2 ENRICHMENT (KPPU + Anti-Selective)
# ═══════════════════════════════════════════════════════
def enrich_h2_kppu():
    """
    H2 hanya punya 8 regulasi. Kita perkaya dengan Google CSE API
    untuk mencari kasus KPPU dan selective enforcement.
    """
    print("\n" + "=" * 60)
    print("5. ENRICHING H2 SELECTIVE ENFORCEMENT (KPPU OSINT)")
    print("=" * 60)
    
    GOOGLE_API_KEY = "AIzaSyCgfjc35Ah1eCVyF8lPLNmpBhX26i5MQrs"
    GOOGLE_CSE_ID = "c369c352f440840cb"
    
    import requests
    import time
    
    queries = [
        'site:kppu.go.id "putusan" "persaingan usaha"',
        'site:kppu.go.id "tender" "persekongkolan"',
        '"penegakan hukum selektif" "investasi" indonesia',
        '"tebang pilih" "hukum" "bisnis" indonesia',
    ]
    
    all_results = []
    url = "https://www.googleapis.com/customsearch/v1"
    
    for q in queries:
        print(f"   [DORK] {q}", end=" ... ")
        try:
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': q,
                'num': 10
            }
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                items = resp.json().get('items', [])
                for item in items:
                    all_results.append({
                        'query': q,
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'url': item.get('link', ''),
                    })
                print(f"Dapat {len(items)} hasil!")
            else:
                print(f"[ERR: {resp.status_code}]")
        except Exception as e:
            print(f"[ERR: {str(e)[:30]}]")
        time.sleep(1)
    
    if all_results:
        df = pd.DataFrame(all_results)
        df = df.drop_duplicates(subset=['url'])
        
        # Extract year
        def ext_yr(row):
            text = f"{row.get('title','')} {row.get('snippet','')}"
            years = re.findall(r'\b(20[0-2]\d)\b', text)
            return int(max(years)) if years else None
        
        df['year'] = df.apply(ext_yr, axis=1)
        df['kategori'] = df['query'].apply(lambda q: 
            'Putusan KPPU' if 'kppu' in q.lower() else 'Penegakan Hukum Selektif')
        
        out = os.path.join(DATA, "h2_kppu_selective_osint.csv")
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"\n   [SAVED] {out} ({len(df)} data unik)")
        print(f"\n   Breakdown:")
        print(df['kategori'].value_counts().to_string())
    else:
        print("   [WARN] Tidak ada data KPPU yang ditemukan.")


# ═══════════════════════════════════════════════════════
# 6. FINAL SUMMARY
# ═══════════════════════════════════════════════════════
def print_final_summary():
    print("\n" + "=" * 60)
    print("ENRICHMENT COMPLETE — FINAL DATA INVENTORY")
    print("=" * 60)
    
    files = [
        ("putusan_ma_enriched.csv", "MA Detail (year, jenis, nomor)", "H1"),
        ("putusan_ma_yearly.csv", "MA Time-series per tahun", "H1"),
        ("putusan_mk_enriched.csv", "MK Detail (year, UU, amar)", "H5"),
        ("putusan_mk_yearly.csv", "MK Time-series per tahun", "H5"),
        ("mk_uu_breakdown.csv", "MK Breakdown UU yang diuji", "H5"),
        ("sipp_merged_enriched.csv", "SIPP Gabungan (Direct+OSINT)", "H3"),
        ("sipp_pn_distribution.csv", "SIPP Distribusi per PN", "H3"),
        ("sipp_yearly.csv", "SIPP Time-series per tahun", "H3"),
        ("sipp_durasi_distribution.csv", "SIPP Bucket durasi proses", "H3"),
        ("regulasi_summary_per_hipotesis.csv", "Regulasi per H1-H5 × status", "H1-H5"),
        ("h2_kppu_selective_osint.csv", "KPPU + Selective OSINT", "H2"),
        ("regulatory_churn_rate.csv", "Churn Rate 52 tahun", "H4"),
        ("h4_reversal_timeline.csv", "Reversal Timeline", "H4"),
        ("laporan_ma_statistik.csv", "MA Statistik Aggregat", "H1,H5"),
    ]
    
    for fname, desc, hip in files:
        fpath = os.path.join(DATA, fname)
        if os.path.exists(fpath):
            rows = len(pd.read_csv(fpath, encoding="utf-8-sig"))
            print(f"   ✅ {fname:45s} | {rows:>5} rows | {hip:6s} | {desc}")
        else:
            print(f"   ❌ {fname:45s} | MISSING | {hip:6s} | {desc}")


if __name__ == "__main__":
    enrich_ma()
    enrich_mk()
    enrich_sipp()
    enrich_regulasi()
    enrich_h2_kppu()
    print_final_summary()
    print("\n✅ DONE. Semua data siap untuk dashboard modeling.")
