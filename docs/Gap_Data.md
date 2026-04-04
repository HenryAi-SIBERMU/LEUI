# Gap Data

### CELIOS LEUI — Per 4 April 2026

> [!CAUTION]
> Dokumen ini mengidentifikasi **SEMUA gap** antara permintaan brief dengan kondisi data dan implementasi dashboard saat ini. Setiap gap harus ditutup atau didokumentasikan sebagai limitasi riset.

---

## 1. Gap Indikator Legal Uncertainty (Tabel A Brief)

Brief meminta 5 indikator kuantitatif. **Tidak satupun** yang bisa diisi dengan data idealnya. Semua menggunakan proxy ekonomi.

| # | Dimensi | Indikator Ideal (Brief) | Status Data Ideal | Proxy yang Dipakai | Kekuatan Proxy | Gap / Risiko |
|---|---------|------------------------|-------------------|-------------------|---------------|-------------|
| 1 | **Inconsistency** | Variansi putusan kasus sejenis | ❌ Tidak ada | Variansi ICOR + Gini distribusi investasi daerah | ⚠️ Sedang | Proxy hanya mengukur *dampak* inkonsistensi (distribusi investasi timpang), bukan *sumber*-nya (putusan pengadilan). Korelasi ≠ kausalitas. |
| 2 | **Selectivity** | Rasio kasus terhadap momentum politik | ❌ Tidak ada | Z-Score anomali IKK/PMI | ⚠️ Sedang | Anomali IKK/PMI bisa disebabkan faktor non-politik (COVID, inflasi global). Tanpa data kasus hukum, tidak bisa membuktikan bahwa drop disebabkan selective enforcement. |
| 3 | **Procedural** | Rata-rata lama penyelesaian kasus | ❌ Tidak ada | ICOR sebagai delay cost + lag correlation | ⚠️ Lemah | ICOR dipengaruhi banyak faktor (infrastruktur, birokrasi, korupsi) — bukan hanya procedural delay pengadilan. |
| 4 | **Reversal** | Jumlah pencabutan izin | ❌ Tidak ada | Spike capital outflow (net sell obligasi) | ⚠️ Sedang | Capital outflow juga dipengaruhi Fed rate, global risk-off, dll. Bukan murni reaksi pencabutan izin. |
| 5 | **Criminalization** | Jumlah kasus pidana bisnis | ❌ Tidak ada | IKK Expectation collapse | ⚠️ Lemah | Collapse IKK bisa disebabkan banyak hal. Tanpa database kasus pidana bisnis, klaim kriminalisasi tetap bersifat inferensial. |

> [!WARNING]
> **Gap Kritis:** Data hukum primer (putusan MA, data PTUN, kasus pidana bisnis, pencabutan izin) **100% tidak tersedia** di dataset saat ini. Seluruh 5 indikator Legal Uncertainty bergantung pada proxy ekonomi yang masing-masing punya kelemahan interpretasi.

---

## 2. Gap Indikator Risk Pricing (Tabel B Brief)

Brief meminta 5 proxy harga risiko. Hanya **1 dari 5** yang datanya tersedia.

| # | Risiko | Proxy Harga (Brief) | Status | Data yang Dibutuhkan | Sumber Potensial |
|---|--------|-------------------|--------|---------------------|-----------------|
| 1 | **Legal risk premium** | Spread bunga pinjaman | ❌ TIDAK ADA | Suku bunga kredit per sektor vs BI rate | Bank Indonesia, OJK, CEIC |
| 2 | **Country risk** | CDS Indonesia | ❌ TIDAK ADA | CDS 5-Year Indonesia (daily) | Bloomberg, Reuters, CEIC |
| 3 | **Investment delay** | Time-to-invest | ⚠️ PARSIAL | Durasi dari izin → realisasi investasi. Dapat di-proxy (lemah) via lag ICOR→realisasi | BKPM (ideal), ICOR (proxy) |
| 4 | **Exit risk** | Capital flight | ✅ ADA | Net sell obligasi harian | `capital_outflow.csv` (32 baris) |
| 5 | **Insurance cost** | Political risk insurance | ❌ TIDAK ADA | Premi asuransi risiko politik Indonesia | MIGA (World Bank), broker asuransi |

> [!WARNING]
> **Gap Kritis:** 3 dari 5 risk pricing indicators **tidak bisa dibangun sama sekali** dari dataset yang ada. 1 bersifat parsial. Hanya Exit Risk yang memiliki data langsung.

---

## 3. Gap Data Kebutuhan Riset (Section 7 Brief)

Brief mengyebutkan 4 kategori data yang dibutuhkan. Berikut status masing-masing:

### 3A. Data Hukum

| Kebutuhan | Status | Keterangan |
|-----------|--------|------------|
| Putusan MA/PT/PTUN | ❌ | Tidak ada dataset. Perlu scraping dari Direktori Putusan MA (putusan3.mahkamahagung.go.id) |
| Data kriminalisasi bisnis | ❌ | Tidak ada database kasus pidana bisnis di Indonesia yang terstruktur |
| Data pencabutan izin | ❌ | Tidak ada. Perlu data dari BKPM/Kementerian terkait |
| Waktu proses perkara | ❌ | Tidak ada. Bisa diekstrak dari Direktori Putusan MA (tanggal registrasi vs tanggal putusan) |

> **Skor: 0/4 tersedia**

### 3B. Data Ekonomi

| Kebutuhan | Status | Keterangan |
|-----------|--------|------------|
| PMA/PMDN per sektor | ✅ | `realisasi_investasi_asing.csv`, `realisasi_investasi_domestik.csv` |
| Cost of capital | ⚠️ | Proxy via ICOR (`icor_nasional.csv`), bukan data spread/bunga langsung |
| CDS Indonesia | ❌ | Tidak ada di dataset |
| Data investasi daerah | ✅ | 394 kab/kota dari file realisasi |

> **Skor: 2/4 tersedia langsung, 1 proxy, 1 tidak ada**

### 3C. Data Persepsi

| Kebutuhan | Status | Keterangan |
|-----------|--------|------------|
| Survei investor | ❌ | Tidak ada. Perlu primary research |
| Wawancara pelaku usaha | ❌ | Tidak ada. Perlu primary research |
| Laporan risk assessment | ❌ | Tidak ada. Bisa menggunakan laporan World Bank Doing Business / EoDB |

> **Skor: 0/3 tersedia**

### 3D. Data Politik

| Kebutuhan | Status | Keterangan |
|-----------|--------|------------|
| Perubahan pejabat | ❌ | Tidak ada dataset terstruktur |
| Momentum pemilu | ❌ | Tidak ada dataset (tanggal pemilu bisa di-hardcode tapi bertentangan dengan prinsip no-hardcode proyek ini) |
| Konflik pusat–daerah | ❌ | Tidak ada dataset terstruktur |

> **Skor: 0/3 tersedia**

---

## 4. Gap Output Riset (Section 9 Brief)

Brief menjanjikan 4 output riset. Berikut status:

| # | Output Dijanjikan | Status | Gap |
|---|------------------|--------|-----|
| 1 | **Legal Risk Pricing Index Indonesia** | ❌ Belum bisa | Membutuhkan minimal 3 dari 5 risk pricing indicators (Tabel B) yang datanya belum ada |
| 2 | **Heatmap Risiko Hukum Investasi** | ⚠️ Parsial | Bisa dibuat heatmap per provinsi dari data investasi, tapi bukan heatmap "risiko hukum" murni |
| 3 | **Policy Paper: Reformasi Penegakan Hukum** | ⚠️ Parsial | Bisa ditulis berdasarkan temuan proxy, tapi klaim akan lemah tanpa data hukum primer |
| 4 | **Early Warning System** | ⚠️ Parsial | Z-Score anomali detection sudah diimplementasikan (H2, H4), tapi hanya untuk indikator ekonomi |

---

## 5. Gap Pertanyaan Riset (Section 8 Brief)

| # | Pertanyaan Riset | Bisa Dijawab? | Keterangan |
|---|-----------------|--------------|------------|
| 1 | Aspek penegakan hukum apa yang paling mahal? | ❌ | Butuh semua 5 indikator Legal Uncertainty + Risk Pricing untuk perbandingan |
| 2 | Apakah ketidakpastian hukum meningkatkan cost of capital? | ⚠️ | Hanya bisa inferensial dari tren ICOR naik, bukan kausal |
| 3 | Hukum buruk vs hukum tak terduga — mana lebih ditakuti? | ❌ | Butuh survei investor (data persepsi) |
| 4 | Apakah efek berbeda antar sektor & daerah? | ✅ | Data realisasi investasi per provinsi tersedia |
| 5 | Bagaimana investor memitigasi risiko hukum? | ❌ | Butuh wawancara/survei (data persepsi) |

---

## 6. Gap Data yang Hanya Berjumlah Kecil

| Dataset | Jumlah Baris | Concern |
|---------|-------------|---------|
| `capital_outflow.csv` | 32 baris | Sangat sedikit untuk anomaly detection. Z-Score kurang reliabel dengan n < 50 |
| `pmi_manufaktur.csv` | 36 baris | Hanya 3 tahun data. Terlalu pendek untuk analisis tren jangka panjang |
| `icor_nasional.csv` | ~15 baris | Data tahunan, sulit untuk lag analysis granular (kuartal) |

---

## 7. Ringkasan Skor Gap + Data yang Perlu Dicari

| Kategori | Tersedia | Proxy | Tidak Ada | % Gap | Data yang Sudah Ada (CSV) | Data yang Perlu Dicari / Ditambahkan |
|----------|----------|-------|-----------|-------|--------------------------|--------------------------------------|
| **Legal Uncertainty (A)** | 0 | 5 | 0 | 100% proxy | Proxy: `icor_nasional.csv`, `data_realisasi_investasi_asing.csv`, `data_realisasi_investasi_domestik.csv`, `ikk_expect_vs_present.csv`, `pmi_manufaktur.csv`, `capital_outflow.csv` | 1. Database putusan MA/PT/PTUN (variansi vonis)<br>2. Database kasus hukum vs timeline politik<br>3. Durasi rata-rata proses perkara (registrasi → putusan)<br>4. Data pencabutan izin dari BKPM/OSS<br>5. Database kasus pidana korporasi/direksi |
| **Risk Pricing (B)** | 1 | 1 | 3 | 80% gap | `capital_outflow.csv` (exit risk)<br>Proxy: `icor_nasional.csv` (investment delay) | 1. Spread suku bunga kredit per sektor (BI/OJK)<br>2. CDS Indonesia 5-Year daily (Bloomberg/CEIC)<br>3. Premi asuransi risiko politik Indonesia (MIGA/broker) |
| **Data Hukum** | 0 | 0 | 4 | 100% gap | — | 1. Putusan MA/PT/PTUN — scraping putusan3.mahkamahagung.go.id<br>2. Data kriminalisasi bisnis — kompilasi manual dari media/pengadilan<br>3. Data pencabutan izin — request ke BKPM<br>4. Waktu proses perkara — ekstrak dari Direktori Putusan MA |
| **Data Ekonomi** | 2 | 1 | 1 | 50% gap | `data_realisasi_investasi_asing.csv` (PMA 394 kab/kota)<br>`data_realisasi_investasi_domestik.csv` (PMDN)<br>Proxy: `icor_nasional.csv` (cost of capital) | 1. CDS Indonesia (sama dengan Risk Pricing #2)<br>2. Suku bunga kredit langsung (bukan proxy ICOR) |
| **Data Persepsi** | 0 | 0 | 3 | 100% gap | — | 1. Survei persepsi investor (primary research, kuesioner)<br>2. Transkrip wawancara pelaku usaha (primary research)<br>3. Laporan risk assessment — World Bank EoDB / UNCTAD WIR |
| **Data Politik** | 0 | 0 | 3 | 100% gap | — | 1. Dataset tanggal perubahan pejabat kunci (manual compile)<br>2. Dataset jadwal pemilu & pilkada (structured timeline)<br>3. Dataset konflik pusat-daerah (manual compile dari media) |
| **Output Riset** | 0 | 3 | 1 | 100% gap | Dashboard H1-H2 sudah jadi (proxy) | 1. Legal Risk Pricing Index — butuh CDS + spread bunga + insurance<br>2. Heatmap Risiko Hukum — butuh data putusan per wilayah<br>3. Policy Paper — butuh data hukum primer untuk klaim kuat<br>4. Early Warning System — butuh real-time data feed |
| **Pertanyaan Riset** | 1 | 1 | 3 | 80% gap | Pertanyaan #4 bisa dijawab dari `data_realisasi_investasi_asing.csv` (per provinsi) | 1. Data semua 5 indikator Legal Uncertainty (untuk perbandingan biaya)<br>2. Survei investor (hukum buruk vs hukum tak terduga)<br>3. Wawancara pelaku usaha (strategi mitigasi risiko hukum) |
| **TOTAL** | **4** | **11** | **18** | | | **12.1% tersedia · 33.3% proxy · 54.5% hard gap** |

> [!IMPORTANT]
> **Kesimpulan:** Dari 33 kebutuhan yang diidentifikasi di brief, **hanya 4 (12.1%)** yang memiliki data langsung. **11 (33.3%)** menggunakan proxy ekonomi yang kekuatan inferensinya terbatas. **18 (54.5%)** sama sekali tidak bisa dipenuhi dari dataset yang ada saat ini.
>
> **Implikasi untuk dashboard:** Dashboard LEUI saat ini adalah **dashboard proxy ekonomi** yang mengukur *dampak* ketidakpastian hukum terhadap indikator ekonomi, bukan mengukur ketidakpastian hukum itu sendiri. Ini harus dikomunikasikan secara transparan.

---

## 8. Rekomendasi Penutupan Gap

### Prioritas Tinggi (Dataset yang bisa diperoleh)
1. **CDS Indonesia 5Y** — Bisa dibeli dari Bloomberg/Reuters/CEIC. Sangat penting untuk Risk Pricing Index.
2. **Suku Bunga Kredit per Sektor** — Tersedia di statistik Bank Indonesia. Kunci untuk legal risk premium.
3. **Data Putusan MA** — Bisa di-scraping dari putusan3.mahkamahagung.go.id (gratis, publik).

### Prioritas Menengah (Butuh effort lebih)
4. **Data pencabutan izin** — Perlu permintaan resmi ke BKPM/OSS.
5. **World Bank Doing Business / EoDB data** — Alternatif untuk risk assessment.

### Prioritas Rendah (Butuh primary research)
6. **Survei investor** — Perlu desain kuesioner dan distribusi.
7. **Political risk insurance premium** — Perlu akses ke data MIGA atau broker.
