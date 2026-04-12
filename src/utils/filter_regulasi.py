"""
KOREKSI #1: Filter regulasi_pasal_id.csv
- Buang semua source = "list_by_year" (dump tahunan tanpa filter)
- Terapkan keyword matching Tier 1
- Terapkan blacklist auto-reject  
- Simpan sebagai regulasi_bisnis_filtered.csv
"""
import pandas as pd
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- Keyword Taxonomy ---
TIER1_KEYWORDS = [
    "investasi", "penanaman modal", "perizinan", "izin usaha",
    "perseroan terbatas", "badan usaha", "modal asing",
    "ketenagakerjaan", "upah", "phk", "hubungan industrial",
    "perdagangan", "ekspor", "impor", "bea cukai", "tarif",
    "pajak", "ppn", "pph", "insentif fiskal", "perpajakan",
    "pertanahan", "hak guna usaha", "hgu", "hgb", "tata ruang", "agraria",
    "minerba", "pertambangan", "migas", "mineral", "energi",
    "perbankan", "pasar modal", "asuransi", "fintech", "ojk",
    "cipta kerja", "omnibus", "oss", "bkpm",
    "pailit", "kepailitan", "pkpu",
    "arbitrase", "penyelesaian sengketa",
    "persaingan usaha", "monopoli", "antimonopoli",
    "hak kekayaan intelektual", "paten", "merek",
    "kawasan ekonomi khusus", "kek", "kawasan industri",
]

BLACKLIST = [
    "pembentukan kabupaten", "pembentukan kota", "pembentukan provinsi",
    "pemilihan umum", "pemilu", "pilkada", "partai politik",
    "narkotika", "terorisme", "korupsi", "tindak pidana",
    "olahraga", "kepemudaan", "keolahragaan",
    "pertahanan", "militer", "tni", "polri", "kepolisian",
    "agama", "wakaf", "zakat", "nikah", "perkawinan",
    "ekstradisi", "kewarganegaraan", "imigrasi",
    "pengelolaan sampah", "penyiaran",
    "anggaran pendapatan", "apbn",  # APBN bukan regulasi bisnis
    "mahkamah konstitusi", "mahkamah agung",  # Kelembagaan
    "jabatan notaris",  # Profesi, bukan bisnis
    "pemerintahan daerah", "otonomi daerah",
]

def is_relevant(title):
    if pd.isna(title):
        return False
    t = title.lower()
    # Auto-reject blacklist
    if any(bl in t for bl in BLACKLIST):
        return False
    # Accept if contains Tier 1 keyword
    return any(kw in t for kw in TIER1_KEYWORDS)

# --- Load ---
df = pd.read_csv('data/processed/regulasi_pasal_id.csv')
print(f"SEBELUM FILTER: {len(df)} baris")
print(f"  source breakdown: {df['source'].value_counts().to_dict()}")

# --- Step 1: Buang list_by_year ---
df_search = df[df['source'] != 'list_by_year'].copy()
print(f"\nSetelah buang list_by_year: {len(df_search)} baris")

# --- Step 2: Dari list_by_year, selamatkan yang RELEVAN ---
df_yearly = df[df['source'] == 'list_by_year'].copy()
df_yearly_relevant = df_yearly[df_yearly['title'].apply(is_relevant)]
print(f"Dari list_by_year, yang relevan keyword: {len(df_yearly_relevant)} baris")

# --- Step 3: Gabungkan ---
df_combined = pd.concat([df_search, df_yearly_relevant], ignore_index=True)

# --- Step 4: Filter ulang semua dengan keyword ---
df_filtered = df_combined[df_combined['title'].apply(is_relevant)].copy()
print(f"\nSetelah keyword filter TOTAL: {len(df_filtered)} baris")

# --- Step 5: Dedup ---
before_dedup = len(df_filtered)
df_filtered = df_filtered.drop_duplicates(subset=['title', 'year'], keep='first')
print(f"Setelah dedup: {len(df_filtered)} (removed {before_dedup - len(df_filtered)})")

# --- Step 6: Sortir ---
df_filtered = df_filtered.sort_values(['year', 'title'], ascending=[False, True])

# --- Save ---
out_path = 'data/processed/regulasi_bisnis_filtered.csv'
df_filtered.to_csv(out_path, index=False, encoding='utf-8-sig')
print(f"\n[SAVED] {out_path} ({len(df_filtered)} baris)")

# --- Tampilkan sample ---
print("\n=== SAMPLE 10 JUDUL (verifikasi relevansi) ===")
for _, row in df_filtered.sample(min(10, len(df_filtered)), random_state=42).iterrows():
    print(f"  [{row['year']}] {row['status']:15s} | {str(row['title'])[:100]}")

# --- Statistik status ---
print(f"\n=== STATUS BREAKDOWN ===")
print(df_filtered['status'].value_counts().to_string())
print(f"\n=== JENIS BREAKDOWN ===")
print(df_filtered['type'].value_counts().to_string())
