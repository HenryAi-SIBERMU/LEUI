# 📂 DATA DIRECTORY — CELIOS5-LEUI

## Struktur Folder

```
data/
├── raw/          ← Hasil scraping mentah, JANGAN SENTUH
├── staging/      ← Hasil enrichment/parsing, untuk debugging
├── final/        ← FILE YANG DIPAKAI DASHBOARD (read-only)
└── processed/    ← [DEPRECATED] folder lama, akan dihapus
```

---

## 🔴 `raw/` — Data Mentah Scraping (8 file)

File hasil langsung dari scraper, BELUM diparse. Kolom masih berupa `query`, `title`, `snippet`, `url`.
**Jangan dipakai langsung untuk visualisasi.**

| File | Rows | Sumber | Catatan |
|------|:----:|--------|---------|
| `putusan_ma_osint.csv` | 89 | Google CSE → MA | Metadata search results saja |
| `putusan_mk_osint.csv` | 47 | Google CSE → MK | Ada `kandidat_nomor` tapi belum diparsing |
| `sipp_nasional_osint.csv` | 45 | Google CSE → SIPP PN | Tidak ada kolom durasi |
| `putusan_sipp_sidoarjo_negara_wanprestasi.csv` | 120 | Direct scrape | Punya `Lama Proses` (hari) |
| `regulasi_pasal_id_raw.csv` | 848 | Pasal.id REST API | Full dump, banyak noise |
| `regulasi_bisnis.csv` | 207 | JDIH BPK | Metadata regulasi bisnis |
| `regulasi_investasi_bisnis.csv` | ~50 | JDIH BPK filtered | Subset investasi |
| `h4_uu_status_chain.csv` | 19 | Pasal.id MCP (gagal) | Semua `error: endpoint_not_found` |

---

## 🟡 `staging/` — Data Hasil Enrichment (7 file)

File hasil parsing dari `enrich_osint_data.py`. Sudah punya kolom terstruktur (`year`, `jenis_perkara`, `amar`, dll).
**Untuk debugging dan audit trail.**

| File | Rows | Diolah Dari | Kolom Tambahan |
|------|:----:|-------------|----------------|
| `putusan_ma_enriched.csv` | 33 | `raw/putusan_ma_osint.csv` | `year`, `jenis_perkara`, `nomor_putusan` |
| `putusan_ma_timeseries.csv` | ~20 | ^ | Aggregat `year × jenis_perkara → jumlah` |
| `putusan_mk_enriched.csv` | 47 | `raw/putusan_mk_osint.csv` | `year`, `uu_diuji`, `amar` |
| `putusan_mk_timeseries.csv` | ~15 | ^ | Aggregat `year × amar → jumlah` |
| `sipp_merged_enriched.csv` | 145 | `raw/sipp_*.csv` (gabungan) | `year`, `pengadilan`, `lama_proses`, `sumber` |
| `regulasi_leui_cleaned.csv` | 170 | `raw/regulasi_pasal_id_raw.csv` | Filtered + `hipotesis` (H1–H5) |
| `h2_kppu_selective_osint.csv` | 30 | Google CSE → KPPU | `year`, `kategori` |

---

## 🟢 `final/` — DATA UNTUK DASHBOARD (21 file)

**INI YANG DIPAKAI STREAMLIT.** Setiap file sudah time-series ready atau aggregat siap chart.

### Variabel Hukum (X) — Layer 1 Dashboard

| File | Rows | Hipotesis | Dipakai Untuk |
|------|:----:|:---------:|---------------|
| `putusan_ma_yearly.csv` | 17 | **H1** | Bar chart volume putusan MA bisnis per tahun |
| `regulasi_h1_yearly.csv` | varies | **H1** | Regulasi H1 per tahun × status |
| `regulasi_h2_yearly.csv` | varies | **H2** | Regulasi H2 per tahun × status |
| `regulasi_h3_yearly.csv` | varies | **H3** | Regulasi H3 per tahun × status |
| `regulasi_h4_yearly.csv` | varies | **H4** | Regulasi H4 per tahun × status |
| `regulasi_h5_yearly.csv` | varies | **H5** | Regulasi H5 per tahun × status |
| `regulasi_summary_per_hipotesis.csv` | 14 | **Exec** | KPI cards per hipotesis |
| `putusan_mk_yearly.csv` | 13 | **H5** | Bar chart judicial review MK per tahun |
| `mk_uu_breakdown.csv` | 14 | **H5** | Donut chart UU yang paling sering diuji |
| `sipp_yearly.csv` | 9 | **H3** | Line chart volume perkara SIPP per tahun |
| `sipp_pn_distribution.csv` | 25 | **H3** | Bar chart distribusi per Pengadilan Negeri |
| `sipp_durasi_distribution.csv` | 5 | **H3** | Histogram bucket durasi proses (hari) |
| `regulatory_churn_rate.csv` | 52 | **H4** | Line chart churn rate 52 tahun (**DUAL AXIS**) |
| `h4_reversal_timeline.csv` | 86 | **H4** | Stacked bar regulasi berlaku/dicabut per tahun |
| `laporan_ma_statistik.csv` | 2 | **H1,H5** | KPI: reversal rate 11.54%, clearance rate |

### Variabel Ekonomi (Y) — Layer 2 Dashboard

| File | Rows | Hipotesis | Dipakai Untuk |
|------|:----:|:---------:|---------------|
| `realisasi_investasi_asing.csv` | ~20K | **H1** | Gini, Std Dev, Top/Bottom Provinsi |
| `realisasi_investasi_domestik.csv` | ~20K | **H1** | Gini, Std Dev |
| `icor_nasional.csv` | ~20 | **H1,H3** | ICOR trend (delay cost) |
| `ikk_expect_vs_present.csv` | ~180 | **H2,H5** | IKK gap, expectation crash |
| `pmi_manufaktur.csv` | ~12 | **H2** | PMI anomaly detection |
| `capital_outflow.csv` | ~12 | **H4** | Net sell obligasi (**DUAL AXIS** dgn churn) |
| `metadata.json` | — | — | Metadata deskripsi dataset |
