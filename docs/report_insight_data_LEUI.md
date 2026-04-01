# 📊 Laporan Insight Data: Risk Pricing Investasi Indonesia

### Sumber: CEIC / CDMNext / Bank Indonesia
### Disusun untuk: CELIOS — Center of Economic and Law Studies
### Tanggal: 31 Maret 2026

---

## 1. Inventaris Data

| # | File | Konten | Sumber | Frekuensi | Periode |
|---|------|--------|--------|-----------|---------|
| 1 | `Biaya Investasi (ICOR).xlsx` | ICOR, PMDN, PMA, GDP Growth | CEIC/CDMNext | Bulanan | 2020–2024 |
| 2 | `Data Realisasi Investasi.xlsx` | PMA/PMDN sub-nasional (394 kab/kota) + Capital Outflow | BKPM + BI | Kuartalan + Harian | 2024–2026 |
| 3 | `Indeks Kepercayaan Konsumen.xlsx` | IKK sub-nasional (PMA/PMDN per kabupaten) | BKPM | Kuartalan | — |
| 4 | `Indeks Kepercayaan Konsumen (Expect vs Present).xlsx` | Consumer Confidence: Expectation vs Present | BI | Bulanan | s/d Nov 2025 |
| 5 | `PMI dan Capital Outflow.xlsx` | Manufacturing PMI S&P + Bond Net Sell | S&P/BI | Bulanan + Harian | 2020–2026 |

---

## 2. Detail Per Dataset

### 2.1 Biaya Investasi (ICOR)

| Parameter | Info |
|---|---|
| **Sheet** | `Chart` (1 sheet, data embed di chart cells) |
| **Shape** | ~27 data rows × 6 kolom |
| **Kolom** | Tanggal, Investasi PMDN, Investasi PMA, GDP Growth (%), ICOR PMDN, ICOR PMA |
| **Unit** | IDR Billion (investasi), ratio (ICOR) |
| **Rentang** | Kuartal 2018 – Desember 2024 |

> [!IMPORTANT]
> ICOR (Incremental Capital-Output Ratio) adalah **proxy cost of capital**. Semakin tinggi ICOR → semakin banyak investasi yang dibutuhkan untuk menghasilkan 1 unit output → **efisiensi investasi rendah**. Dalam konteks LEUI, ICOR tinggi bisa mengindikasikan "risk premium" yang dibebankan investor.

**Insight awal:**
- ICOR PMA biasanya lebih tinggi dari ICOR PMDN → investor asing membutuhkan return lebih tinggi
- Tren ICOR 2020 (pandemi) sangat anomali — perlu diisolasi
- Korelasi ICOR ↔ legal uncertainty events (regulatory changes) bisa diuji

---

### 2.2 Data Realisasi Investasi (Sub-Nasional)

| Parameter | Info |
|---|---|
| **Sheet 1** | `My Series` — PMA/PMDN per kabupaten |
| **Shape** | ~172 rows × 394 kolom |
| **Kolom** | Tanggal + 393 seri kabupaten/kota |
| **Format** | `Investment Realization: Foreign: [Prov]: [Kab/Kota]` |
| **Unit** | IDR Billion |
| **Frekuensi** | Kuartalan |

| Parameter | Info |
|---|---|
| **Sheet 2** | `Capital Outflow` — Bond Net Sell |
| **Shape** | 61 rows × 2 kolom |
| **Variable** | `Foreign Capital Flow: Non-Resident Transaction: Net Sell` |
| **Unit** | IDR Trillion |
| **Frekuensi** | Harian (5 obs/minggu) |
| **Rentang** | Des 2024 – Jan 2026 |
| **Sumber** | Bank Indonesia |

> [!WARNING]
> Capital Outflow (Net Sell) adalah **sinyal langsung capital flight**. Semakin tinggi Net Sell → investor asing menarik dana dari pasar obligasi Indonesia → indikasi **risk aversion** meningkat. Mean: 8.13 IDR tn, Max spike: 24.04 IDR tn.

---

### 2.3 Indeks Kepercayaan Konsumen (IKK) — Sub-Nasional

| Parameter | Info |
|---|---|
| **Sheet** | `My Series` |
| **Shape** | 172 rows × 394 kolom |
| **Konten** | Realisasi investasi per kabupaten/kota (PMA + PMDN) |
| **Format** | Sama dengan file #2 — kemungkinan **dataset induk** yang lebih lengkap |

> [!NOTE]
> Meskipun nama file "Indeks Kepercayaan Konsumen", isinya adalah data **realisasi investasi sub-nasional** dari CDMNext. Kemungkinan file salah label, atau merupakan bundle data dari platform CEIC yang mencakup multiple series. Perlu dikonfirmasi.

---

### 2.4 IKK: Expectation vs Present Situation

| Parameter | Info |
|---|---|
| **Sheet** | `My Series` |
| **Shape** | 326 rows × 3 kolom |
| **Kolom 1** | `Consumer Confidence: Expectation: Consumer Survey: SA` |
| **Kolom 2** | `Consumer Confidence: Current Economic Condition: Consumer Survey: SA` |
| **Unit** | Index |
| **Frekuensi** | Bulanan |
| **Rentang** | s/d November 2025 |
| **Sumber** | Bank Indonesia (Consumer Survey) |

> [!IMPORTANT]
> Gap antara **Expectation** dan **Present** mengukur **sentimen forward-looking** konsumen. Jika Expectation >> Present → konsumen masih optimis. Jika gap menyempit/berbalik → kepercayaan terkikis. Dalam konteks LEUI: penurunan IKK bisa berkorelasi dengan peristiwa ketidakpastian hukum.

**Potensi analisis:**
- Overlay IKK trend dengan timeline peristiwa hukum besar (revisi UU, kriminalisasi bisnis)
- Scatter: IKK vs investment realization per periode
- Gap (Expectation − Present) sebagai leading indicator

---

### 2.5 PMI & Capital Outflow

| Parameter | Info |
|---|---|
| **Sheet 1** | `PMI Manufaktur S&P` |
| **Variable** | S&P Global Manufacturing PMI Indonesia |
| **Shape** | ~65 rows |
| **Unit** | Index (50 = netral) |
| **Frekuensi** | Bulanan |
| **Sumber** | S&P Global / IHS Markit |

| Parameter | Info |
|---|---|
| **Sheet 2** | `Capital Outflow` — sama dengan file #2 Sheet 2 |
| **Duplikat** dari `Data Realisasi Investasi.xlsx` Sheet `Capital Outflow` |

> [!TIP]
> PMI >50 = ekspansi manufaktur; PMI <50 = kontraksi. Dalam LEUI framework, PMI is a **leading indicator** aktivitas ekonomi riil. Jika legal uncertainty meningkat → PMI drop (manufacturer menunda ekspansi) → capital outflow meningkat.

---

## 3. Mapping Data → Framework LEUI

| Data Tersedia | Posisi dalam Framework | Hipotesis |
|---|---|---|
| ICOR (PMDN, PMA) | **Cost of Capital** — H3 (Procedural) | Enforcement risk ↔ Cost of capital ↑ |
| Capital Outflow (Net Sell) | **Capital Flight** — H4 (Reversal) | Regulatory reversal → exit risk |
| PMI Manufaktur | **Business Activity** — H1 (Inconsistency) | Uncertainty → production delay |
| IKK (Expectation vs Present) | **Investor/Consumer Sentiment** — H2 (Selective) | Selective enforcement → confidence drop |
| Realisasi Investasi Sub-Nasional | **Investment Behavior** — semua H | Pricing of risk → investment decision |

---

## 4. Data Gap — Yang Belum Tersedia

| Dibutuhkan (dari brief) | Status | Keterangan |
|---|---|---|
| Putusan MA/PT/PTUN | ❌ Belum ada | Data hukum primer — sulit diakses |
| Data kriminalisasi bisnis | ❌ Belum ada | Jumlah kasus pidana direksi/investor |
| Data pencabutan izin | ❌ Belum ada | Regulatory reversal events |
| CDS Indonesia | ❌ Belum ada | Country risk premium (Bloomberg/Reuters) |
| Survei investor | ❌ Belum ada | Perception data (kuisioner) |
| Waktu proses perkara | ❌ Belum ada | Process risk metric |

> [!CAUTION]
> Dari 12 kategori data yang dicanangkan di brief, baru **5 yang tersedia** (ekonomi/makro). Semua data **hukum primer** dan **persepsi** belum ada. Ini berarti dashboard pertama akan fokus pada **Risk Pricing Channel** (cost of capital, capital flight, sentimen) bukan Legal Enforcement Quality Index secara langsung.

---

## 5. Rekomendasi Strategi Data

### Fase 1 (Sekarang — dengan data yang ada):
> Bangun dashboard **"Investment Risk Barometer"** berbasis data makro-ekonomi yang sudah tersedia (ICOR, PMI, IKK, Capital Outflow, Realisasi Investasi). Overlay dengan timeline peristiwa hukum untuk visualisasi korelasi.

### Fase 2 (Pengembangan):
> Tambahkan layer data hukum (putusan, kriminalisasi, pencabutan izin) seiring ketersediaan data.

### Fase 3 (Indeks):
> Konstruksi LEUI composite index yang menggabungkan data ekonomi + data hukum.
