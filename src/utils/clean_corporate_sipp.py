import pandas as pd
import numpy as np
import os

def process_corporate_sipp():
    print("=" * 60)
    print("SIPP CORPORATE FILTER & FULL AGGREGATOR")
    print("Menerapkan MACRO-LEVEL LEGAL PROXY (Corporate Taxonomy)")
    print("=" * 60)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    input_file = os.path.join(base_dir, "data", "processed", "sipp_nasional_wanprestasi_massal.csv")
    final_dir = os.path.join(base_dir, "data", "final")
    os.makedirs(final_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print("[ERROR] File mentah tidak ditemukan: " + input_file)
        return

    print("Mengimpor data mentah dari CSV...")
    df = pd.read_csv(input_file, dtype=str)
    df['durasi_hari'] = pd.to_numeric(df.get('durasi_hari', pd.Series(dtype=float)), errors='coerce').fillna(0)
    df_awal = len(df)
    print("Total Data Mentah: {:,} perkara".format(df_awal))

    df = df.dropna(subset=['Para Pihak'])

    # ── TAXONOMY FILTER ──
    keywords = [
        r'\bPT\b', r'PT\.', r'\bCV\b', r'CV\.', r'\bKOPERASI\b',
        r'\bYAYASAN\b', r'\bBANK\b', r'\bBPR\b', r'\bPEMERINTAH\b',
        r'\bKEMENTERIAN\b', r'\bMENTERI\b', r'\bBUPATI\b',
        r'\bGUBERNUR\b', r'\bWALIKOTA\b', r'\bDINAS\b', r'\bFIRMA\b', r'\bFA\b'
    ]
    pattern = '|'.join(keywords)
    print("Memfilter data korporasi...")
    df_corp = df[df['Para Pihak'].str.contains(pattern, case=False, na=False, regex=True)].copy()
    
    # FILTER OUT NOISE 'KATABAY'
    df_corp = df_corp[~df_corp['Para Pihak'].str.contains(r'KATABAY', case=False, na=False)]
    
    df_akhir = len(df_corp)
    pct = (df_akhir / df_awal) * 100 if df_awal > 0 else 0
    print("Total Data Korporasi: {:,} perkara ({:.1f}%)".format(df_akhir, pct))

    # Filter durasi valid (1-1000 hari)
    df_corp = df_corp[(df_corp['durasi_hari'] > 0) & (df_corp['durasi_hari'] <= 1000)]
    print("Setelah filter durasi valid: {:,} perkara".format(len(df_corp)))

    # ── OUTPUT 1: Dataset Korporasi Lengkap ──
    out1 = os.path.join(final_dir, "sipp_corporate_wanprestasi.csv")
    df_corp.to_csv(out1, index=False, encoding='utf-8-sig')
    print("[SAVED] sipp_corporate_wanprestasi.csv")

    # ── OUTPUT 2: Distribusi per PN (Bar Chart) ──
    agg_pn = df_corp.groupby('Pengadilan').agg(
        Avg_Lama_Proses=('durasi_hari', 'mean'),
        jumlah=('Pengadilan', 'count')
    ).reset_index()
    # Rename kolom agar konsisten dengan expectasi H1
    agg_pn.columns = ['pengadilan', 'Avg_Lama_Proses', 'jumlah']
    agg_pn = agg_pn.sort_values(by='jumlah', ascending=False)
    out2 = os.path.join(final_dir, "sipp_pn_distribution.csv")
    agg_pn.to_csv(out2, index=False, encoding='utf-8-sig')
    print("[SAVED] sipp_pn_distribution.csv ({} PN)".format(len(agg_pn)))

    # ── OUTPUT 3: Distribusi Durasi (Continuous Daily) ──
    agg_durasi = df_corp.groupby('durasi_hari').size().reset_index(name='jumlah')
    agg_durasi = agg_durasi.sort_values('durasi_hari')
    out3 = os.path.join(final_dir, "sipp_durasi_distribution.csv")
    agg_durasi.to_csv(out3, index=False, encoding='utf-8-sig')
    print("[SAVED] sipp_durasi_distribution.csv (Granular Daily Data)")

    # ── OUTPUT 4: Yearly Aggregat ──
    df_corp['Tanggal Daftar'] = pd.to_datetime(df_corp['Tanggal Daftar'], format='%d %b %Y', errors='coerce')
    df_with_date = df_corp.dropna(subset=['Tanggal Daftar']).copy()
    df_with_date['year'] = df_with_date['Tanggal Daftar'].dt.year
    agg_yearly = df_with_date.groupby('year').agg(
        avg_durasi_hari=('durasi_hari', 'mean'),
        total_perkara=('year', 'count')
    ).reset_index()
    agg_yearly = agg_yearly.sort_values('year')
    out4 = os.path.join(final_dir, "sipp_yearly.csv")
    agg_yearly.to_csv(out4, index=False, encoding='utf-8-sig')
    print("[SAVED] sipp_yearly.csv")
    for _, row in agg_yearly.iterrows():
        print("  {} : {:,} perkara (avg {:.0f} hari)".format(int(row['year']), int(row['total_perkara']), row['avg_durasi_hari']))

    # ── OUTPUT 5: Monthly Aggregat ──
    df_with_date['YearMonth'] = df_with_date['Tanggal Daftar'].dt.to_period('M').astype(str)
    agg_monthly = df_with_date.groupby('YearMonth').size().reset_index(name='Jumlah_Kasus')
    agg_monthly = agg_monthly.sort_values('YearMonth')
    out5 = os.path.join(final_dir, "sipp_wanprestasi_monthly.csv")
    agg_monthly.to_csv(out5, index=False, encoding='utf-8-sig')
    print("[SAVED] sipp_wanprestasi_monthly.csv ({} bulan)".format(len(agg_monthly)))

    print("=" * 60)
    print("SELESAI! Semua file agregat telah di-regenerasi dari {} perkara korporasi.".format(len(df_corp)))
    print("=" * 60)

if __name__ == "__main__":
    process_corporate_sipp()
