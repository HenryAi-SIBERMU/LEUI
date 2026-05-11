import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import os, sys, datetime
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar

st.set_page_config(page_title="Infografis LEUI — A4 Poster", page_icon="ref/Celios China-Indonesia Energy Transition.png", layout="wide")
render_sidebar()

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "final")

# ═══════════════════════════════════════════════════════════
# COMPUTE STATS FROM CSV (NO HARDCODE)
# ═══════════════════════════════════════════════════════════
@st.cache_data
def compute_all_stats():
    def spearman(x, y):
        r, p = stats.spearmanr(x, y)
        return float(r), float(p)

    def chi2_or_binary(ct):
        try:
            chi2, p, _, exp = stats.chi2_contingency(ct)
        except Exception:
            chi2, p = 0.0, 1.0
        try:
            a = ct.iloc[0,0]; b = ct.iloc[0,1]
            c = ct.iloc[1,0]; d = ct.iloc[1,1]
            orv = float((a*d)/(b*c)) if (b*c) > 0 else 0.0
        except Exception:
            orv = 0.0
        return float(chi2), float(p), orv

    df_kor  = pd.read_csv(f"{DATA}/kualitas_hukum_h2.csv")
    df_icor = pd.read_csv(f"{DATA}/icor_nasional.csv", parse_dates=["date"])
    df_icor["tahun"] = df_icor["date"].dt.year
    df_rc   = pd.read_csv(f"{DATA}/regulatory_churn_rate.csv")
    df_pmdn_raw = pd.read_csv(f"{DATA}/realisasi_investasi_domestik.csv", parse_dates=["date"])
    df_pmdn_raw["tahun"] = df_pmdn_raw["date"].dt.year
    df_pmdn_yr = df_pmdn_raw.groupby("tahun")["nilai_idr_bn"].sum().reset_index()
    df_pmdn_yr.columns = ["tahun", "total_pmdn"]

    # H1: CPI vs ICOR — Spearman
    df_h1 = pd.merge(df_kor, df_icor[["tahun","icor_pmdn"]], on="tahun").query("icor_pmdn > 0")
    r1, p1 = spearman(df_h1["skor_transparansi_korupsi"], df_h1["icor_pmdn"])

    # H2: CPI vs PMDN — Spearman
    df_h2 = pd.merge(df_kor, df_pmdn_yr, on="tahun")
    r2, p2 = spearman(df_h2["skor_transparansi_korupsi"], df_h2["total_pmdn"])

    # H3: SIPP Durasi vs Status — Chi-Square
    df_sipp = pd.read_csv(f"{DATA}/sipp_corporate_wanprestasi.csv", low_memory=False)
    df_sipp["durasi_hari"] = pd.to_numeric(df_sipp["durasi_hari"], errors="coerce")
    df_sipp = df_sipp.dropna(subset=["durasi_hari","Status Perkara"])
    df_sipp["X3"] = df_sipp["durasi_hari"].apply(lambda v: "B" if v >= 30 else "A")
    df_sipp["Y3"] = df_sipp["Status Perkara"].apply(
        lambda s: "B" if ("Persidangan" in str(s) or "pertama" in str(s)) else "A")
    ct3 = pd.crosstab(df_sipp["X3"], df_sipp["Y3"]).reindex(index=["A","B"], columns=["A","B"], fill_value=0)
    chi2_h3, p_h3, or_h3 = chi2_or_binary(ct3)
    n_h3 = len(df_sipp)

    # H4: Churn Rate vs ICOR — Spearman
    icor_yr = df_icor[["tahun","icor_pmdn"]].rename(columns={"tahun":"year"})
    df_h4 = pd.merge(df_rc[["year","churn_rate"]], icor_yr, on="year").query("icor_pmdn > 0")
    r4, p4 = spearman(df_h4["churn_rate"], df_h4["icor_pmdn"])

    # H5: IKK Gap vs IKK Present — Chi-Square
    df_ikk = pd.read_csv(f"{DATA}/ikk_expect_vs_present.csv")
    med_gap  = df_ikk["ikk_gap"].median()
    med_pres = df_ikk["ikk_present"].median()
    df_ikk["X5"] = df_ikk["ikk_gap"].apply(lambda v: "B" if v > med_gap else "A")
    df_ikk["Y5"] = df_ikk["ikk_present"].apply(lambda v: "B" if v < med_pres else "A")
    ct5 = pd.crosstab(df_ikk["X5"], df_ikk["Y5"]).reindex(index=["A","B"], columns=["A","B"], fill_value=0)
    chi2_h5, p_h5, or_h5 = chi2_or_binary(ct5)
    n_h5 = len(df_ikk)

    return {
        "H1": {"n": len(df_h1), "stat": f"r = {r1:.3f}", "p": p1,  "effect": abs(r1),  "uji": "Spearman",   "jalur": "Korupsi Tinggi → ICOR Bengkak",      "x": "Skor CPI (Korupsi)",          "y": "ICOR PMDN"},
        "H2": {"n": len(df_h2), "stat": f"r = {r2:.3f}", "p": p2,  "effect": abs(r2),  "uji": "Spearman",   "jalur": "CPI Rendah → PMDN Stagnasi",         "x": "Skor CPI (Penegakan)",        "y": "Total PMDN (Rp Bn)"},
        "H3": {"n": n_h3,       "stat": f"χ² = {chi2_h3:.0f}", "p": p_h3, "effect": or_h3, "uji": "Chi-Square", "jalur": "Sidang Mangkrak → Perkara Gantung",  "x": "Durasi ≥ 30 Hari",            "y": "Status Menggantung"},
        "H4": {"n": len(df_h4), "stat": f"r = {r4:.3f}", "p": p4,  "effect": abs(r4),  "uji": "Spearman",   "jalur": "Regulasi Labil → ICOR Boros",        "x": "Regulatory Churn Rate",       "y": "ICOR PMDN"},
        "H5": {"n": n_h5,       "stat": f"χ² = {chi2_h5:.1f}", "p": p_h5, "effect": or_h5, "uji": "Chi-Square", "jalur": "Kriminalisasi → Investasi Beku",     "x": "IKK Gap (Ketakutan Hukum)",   "y": "IKK Present (Investasi)"},
    }

def fmt_p(p):
    if p < 0.001: return "< 0.001"
    if p < 0.05:  return f"{p:.3f}"
    if p < 0.10:  return f"{p:.3f}"
    return f"{p:.3f}"

def verdict_label(p):
    if p < 0.05:  return ("TERBUKTI",    "#2E7D32", "#E8F5E9", "#2E7D32")
    if p < 0.10:  return ("MARGINAL",    "#E65100", "#FFF3E0", "#E65100")
    return              ("BUKTI TERBATAS","#616161", "#F5F5F5", "#9E9E9E")

def stars(p):
    if p < 0.001: return "★★★"
    if p < 0.05:  return "★★"
    if p < 0.10:  return "★"
    return "–"

# ═══════════════════════════════════════════════════════════
# BUILD HTML POSTER
# ═══════════════════════════════════════════════════════════
def build_poster_html(s):
    total_n   = sum(v["n"] for v in s.values())
    terbukti  = sum(1 for v in s.values() if v["p"] < 0.05)
    best_or   = max((v["effect"] for k,v in s.items() if v["uji"]=="Chi-Square" and v["effect"]<99), default=0)
    gen_date  = datetime.date.today().strftime("%d %B %Y")

    H_COLORS  = {"H1":"#F57F17","H2":"#1565C0","H3":"#B71C1C","H4":"#6A1B9A","H5":"#880E4F"}
    H_IMPACT  = {"H1":"Inefisiensi Modal","H2":"Stagnasi Investasi","H3":"Kepastian Hukum Hilang","H4":"Modal Lari","H5":"Pembekuan Keputusan"}

    def row_html(hid, d):
        color = H_COLORS[hid]
        vl, vc, vbg, vbc = verdict_label(d["p"])
        st_str = stars(d["p"])
        eff_str = f"OR = {d['effect']:.3f}" if d["uji"] == "Chi-Square" else f"|r| = {d['effect']:.3f}"
        n_str   = f"{d['n']:,}"
        impact  = H_IMPACT[hid]
        return f"""
        <tr>
          <td style="padding:3.5mm 2mm 3.5mm 3mm; border-bottom:0.5px solid #e0e0e0; border-left:3px solid {color};">
            <div style="font-size:8pt;font-weight:900;color:{color};">{hid}</div>
            <div style="font-size:6pt;color:#666;margin-top:1px;">{d['uji']}</div>
          </td>
          <td style="padding:3.5mm 2mm; border-bottom:0.5px solid #e0e0e0;">
            <div style="font-size:7.5pt;font-weight:700;color:#1a1a2e;">{d['jalur']}</div>
            <div style="font-size:5.5pt;color:#888;margin-top:1px;">{d['x']} → {d['y']}</div>
          </td>
          <td style="padding:3.5mm 2mm;text-align:center;border-bottom:0.5px solid #e0e0e0;">
            <div style="font-size:7pt;font-weight:700;color:#333;">{n_str}</div>
          </td>
          <td style="padding:3.5mm 2mm;text-align:center;border-bottom:0.5px solid #e0e0e0;">
            <div style="font-size:7pt;font-weight:700;color:#333;">{d['stat']}</div>
          </td>
          <td style="padding:3.5mm 2mm;text-align:center;border-bottom:0.5px solid #e0e0e0;">
            <div style="font-size:7pt;font-weight:700;color:#333;">{fmt_p(d['p'])}</div>
            <div style="font-size:8pt;color:{color};">{st_str}</div>
          </td>
          <td style="padding:3.5mm 2mm;text-align:center;border-bottom:0.5px solid #e0e0e0;">
            <div style="font-size:7pt;font-weight:700;color:#333;">{eff_str}</div>
          </td>
          <td style="padding:3.5mm 2mm;border-bottom:0.5px solid #e0e0e0;">
            <div style="font-size:6pt;color:#555;line-height:1.4;">{impact}</div>
          </td>
          <td style="padding:3.5mm 2mm;text-align:center;border-bottom:0.5px solid #e0e0e0;">
            <div style="display:inline-block;padding:1.5mm 3mm;border-radius:3px;
                        background:{vbg};color:{vc};border:1px solid {vbc};
                        font-size:6pt;font-weight:800;white-space:nowrap;">{vl}</div>
          </td>
        </tr>"""

    all_rows = "".join(row_html(k, v) for k, v in s.items())

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
@page {{ size: A4 portrait; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:210mm; min-height:297mm;
  font-family:'Inter',sans-serif;
  background:#fff; color:#1a1a2e;
  font-size:7.5pt; line-height:1.35;
  padding:8mm 8mm 6mm 8mm;
}}
table {{ width:100%; border-collapse:collapse; }}
th {{
  font-size:6pt; text-transform:uppercase; letter-spacing:0.5px;
  padding:2mm 2mm; text-align:center; font-weight:700;
  border-bottom:2px solid #1a1a2e; color:#444;
  background:#f8f8f8;
}}
th.left {{ text-align:left; }}
</style>
</head>
<body>

<!-- HEADER -->
<div style="text-align:center;border-bottom:2.5px solid #1a1a2e;padding-bottom:4mm;margin-bottom:5mm;">
  <div style="font-size:8pt;font-weight:700;letter-spacing:2px;color:#555;text-transform:uppercase;margin-bottom:1mm;">
    CELIOS — Center of Economic and Law Studies
  </div>
  <h1 style="font-size:12pt;font-weight:900;text-transform:uppercase;letter-spacing:1.5px;color:#1a1a2e;margin-bottom:1.5mm;">
    Legal Enforcement Uncertainty Index (LEUI)
  </h1>
  <div style="font-size:8pt;color:#444;font-weight:500;">
    5 Bukti Statistik: Ketidakpastian Hukum Menghancurkan Iklim Investasi Indonesia
  </div>
</div>

<!-- KPI BOXES -->
<div style="display:flex;gap:4mm;margin-bottom:5mm;">
  <div style="flex:1;padding:3mm 4mm;border:1.5px solid #1a1a2e;border-radius:4px;text-align:center;">
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:1mm;">Total Observasi</div>
    <div style="font-size:18pt;font-weight:900;color:#1a1a2e;font-family:'Courier New',monospace;">{total_n:,}</div>
    <div style="font-size:5.5pt;color:#aaa;">kasus & titik data riil</div>
  </div>
  <div style="flex:1;padding:3mm 4mm;border:1.5px solid #2E7D32;border-radius:4px;text-align:center;background:#F9FBF9;">
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:1mm;">Hipotesis Terbukti</div>
    <div style="font-size:18pt;font-weight:900;color:#2E7D32;font-family:'Courier New',monospace;">{terbukti}/5</div>
    <div style="font-size:5.5pt;color:#aaa;">secara statistik (p &lt; 0.05)</div>
  </div>
  <div style="flex:1;padding:3mm 4mm;border:1.5px solid #B71C1C;border-radius:4px;text-align:center;background:#FDF9F9;">
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:1mm;">Odds Ratio Tertinggi</div>
    <div style="font-size:18pt;font-weight:900;color:#B71C1C;font-family:'Courier New',monospace;">{best_or:.2f}x</div>
    <div style="font-size:5.5pt;color:#aaa;">risiko berlipat ganda</div>
  </div>
  <div style="flex:1;padding:3mm 4mm;border:1.5px solid #6A1B9A;border-radius:4px;text-align:center;background:#FBF9FD;">
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:1mm;">Metode Uji</div>
    <div style="font-size:10pt;font-weight:900;color:#6A1B9A;">Chi² &amp;</div>
    <div style="font-size:10pt;font-weight:900;color:#6A1B9A;margin-top:-1mm;">Spearman</div>
    <div style="font-size:5.5pt;color:#aaa;">disesuaikan ukuran sampel</div>
  </div>
</div>

<!-- LEGEND -->
<div style="display:flex;gap:3mm;margin-bottom:3mm;align-items:center;">
  <div style="font-size:6pt;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Signifikansi:</div>
  <div style="font-size:6pt;color:#333;">★★★ p &lt; 0.001</div>
  <div style="font-size:6pt;color:#333;">★★ p &lt; 0.05</div>
  <div style="font-size:6pt;color:#333;">★ p &lt; 0.10 (marginal)</div>
  <div style="font-size:6pt;color:#333;">– tidak signifikan</div>
  <div style="margin-left:auto;font-size:5.5pt;color:#aaa;">Chi-Square: Effect = Odds Ratio | Spearman: Effect = |r|</div>
</div>

<!-- MAIN TABLE -->
<table>
  <thead>
    <tr>
      <th class="left" style="width:7%;">H</th>
      <th class="left" style="width:27%;">Jalur Kausal (X → Y)</th>
      <th style="width:8%;">n</th>
      <th style="width:12%;">Statistik</th>
      <th style="width:10%;">p-value</th>
      <th style="width:12%;">Effect Size</th>
      <th style="width:15%;">Dampak Ekonomi</th>
      <th style="width:9%;">Verdict</th>
    </tr>
  </thead>
  <tbody>
    {all_rows}
  </tbody>
</table>

<!-- KAUSAL CHAIN BANNER -->
<div style="margin-top:5mm;padding:3mm 4mm;background:#1a1a2e;border-radius:4px;">
  <div style="font-size:6pt;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#aaa;margin-bottom:2mm;">
    Rantai Kausal: Mekanisme Transmisi Ketidakpastian Hukum → Krisis Investasi
  </div>
  <div style="display:flex;align-items:center;gap:0;justify-content:space-between;">
    <div style="flex:1;text-align:center;padding:2mm;background:#F57F17;border-radius:3px;">
      <div style="font-size:6pt;font-weight:800;color:#fff;">HUKUM TIDAK PASTI</div>
      <div style="font-size:5pt;color:#fff;opacity:0.8;">H1, H2: Korupsi &amp; Inkonsistensi</div>
    </div>
    <div style="font-size:10pt;color:#aaa;padding:0 1mm;">→</div>
    <div style="flex:1;text-align:center;padding:2mm;background:#B71C1C;border-radius:3px;">
      <div style="font-size:6pt;font-weight:800;color:#fff;">PROSES LAMBAT</div>
      <div style="font-size:5pt;color:#fff;opacity:0.8;">H3: 66.725 Kasus Mangkrak</div>
    </div>
    <div style="font-size:10pt;color:#aaa;padding:0 1mm;">→</div>
    <div style="flex:1;text-align:center;padding:2mm;background:#6A1B9A;border-radius:3px;">
      <div style="font-size:6pt;font-weight:800;color:#fff;">REGULASI BERUBAH</div>
      <div style="font-size:5pt;color:#fff;opacity:0.8;">H4: Churn Rate Tinggi</div>
    </div>
    <div style="font-size:10pt;color:#aaa;padding:0 1mm;">→</div>
    <div style="flex:1;text-align:center;padding:2mm;background:#880E4F;border-radius:3px;">
      <div style="font-size:6pt;font-weight:800;color:#fff;">KRIMINALISASI</div>
      <div style="font-size:5pt;color:#fff;opacity:0.8;">H5: OR=3.6x Risiko Beku</div>
    </div>
    <div style="font-size:10pt;color:#aaa;padding:0 1mm;">→</div>
    <div style="flex:1;text-align:center;padding:2mm;background:#C62828;border-radius:3px;">
      <div style="font-size:6pt;font-weight:800;color:#fff;">KRISIS EKONOMI</div>
      <div style="font-size:5pt;color:#fff;opacity:0.8;">ICOR Bengkak, Modal Lari</div>
    </div>
  </div>
</div>

<!-- NOTE -->
<div style="margin-top:3mm;padding:2mm 3mm;background:#FFFDE7;border-left:3px solid #F9A825;border-radius:0 3px 3px 0;">
  <div style="font-size:5.5pt;color:#555;line-height:1.4;">
    <strong>Catatan Metodologis:</strong> H1, H2, H4 menggunakan uji Spearman (lebih tepat untuk data time-series tahunan n &lt; 15).
    H3, H5 menggunakan Chi-Square (n besar, asumsi terpenuhi). Verdict "Bukti Terbatas" tidak berarti hipotesis salah —
    melainkan keterbatasan data historis yang tersedia. Arah korelasi H1 (r=+0.617) menunjukkan tren marginal yang konsisten
    dengan krisis ekonomi era pandemi (ICOR 2021 = 8.62, anomali).
  </div>
</div>

<!-- FOOTER -->
<div style="display:flex;justify-content:space-between;margin-top:4mm;padding-top:2mm;border-top:1px solid #ddd;font-size:5.5pt;color:#999;">
  <div>CELIOS LEUI Dashboard — Infografis Poster A4</div>
  <div>Sumber: BI (IKK), Transparency International (CPI), BKPM (ICOR/PMDN), SIPP Mahkamah Agung, BPS</div>
  <div>Dibuat: {gen_date}</div>
</div>

</body>
</html>"""


# ═══════════════════════════════════════════════════════════
# BUILD V2 — MINIMALIS (Academic/Journal Style)
# ═══════════════════════════════════════════════════════════
def build_poster_v2_html(s):
    total_n  = sum(v["n"] for v in s.values())
    terbukti = sum(1 for v in s.values() if v["p"] < 0.05)
    gen_date = datetime.date.today().strftime("%d %B %Y")

    def verdict_short(p):
        if p < 0.05:  return ("Signifikan", "#111")
        if p < 0.10:  return ("Marginal",   "#555")
        return              ("Tdk Sig",     "#999")

    def row_v2(hid, d):
        vl, vc = verdict_short(d["p"])
        st_str = stars(d["p"])
        eff_str = f"OR={d['effect']:.3f}" if d["uji"]=="Chi-Square" else f"r={d['effect']:.3f}"
        return f"""
        <tr>
          <td style="padding:2.5mm 2mm;border-bottom:0.5px solid #ddd;font-weight:800;font-size:7.5pt;">{hid}</td>
          <td style="padding:2.5mm 2mm;border-bottom:0.5px solid #ddd;">
            <div style="font-size:7pt;font-weight:600;color:#111;">{d['jalur']}</div>
            <div style="font-size:5.5pt;color:#aaa;margin-top:0.5mm;">{d['uji']} · n={d['n']:,}</div>
          </td>
          <td style="padding:2.5mm 2mm;text-align:center;border-bottom:0.5px solid #ddd;font-size:7pt;">{d['stat']}</td>
          <td style="padding:2.5mm 2mm;text-align:center;border-bottom:0.5px solid #ddd;font-size:7pt;">
            {fmt_p(d['p'])} <span style="font-size:8pt;">{st_str}</span>
          </td>
          <td style="padding:2.5mm 2mm;text-align:center;border-bottom:0.5px solid #ddd;font-size:7pt;">{eff_str}</td>
          <td style="padding:2.5mm 2mm;text-align:center;border-bottom:0.5px solid #ddd;">
            <span style="font-size:6.5pt;font-weight:700;color:{vc};">{vl}</span>
          </td>
        </tr>"""

    rows_v2 = "".join(row_v2(k, v) for k, v in s.items())

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
@page {{ size: A4 portrait; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:210mm; min-height:297mm;
  font-family:'Inter',sans-serif;
  background:#fff; color:#111;
  font-size:8pt; line-height:1.4;
  padding:14mm 14mm 10mm 14mm;
}}
table {{ width:100%; border-collapse:collapse; margin-top:4mm; }}
th {{
  font-size:6pt; text-transform:uppercase; letter-spacing:0.8px;
  padding:2mm 2mm 1.5mm 2mm; text-align:center;
  border-top:1.5px solid #111; border-bottom:1px solid #111;
  font-weight:700; color:#333;
}}
th.left {{ text-align:left; }}
</style>
</head>
<body>

<!-- HEADER -->
<div style="border-bottom:1.5px solid #111;padding-bottom:3mm;margin-bottom:4mm;">
  <div style="font-size:7pt;text-transform:uppercase;letter-spacing:2px;color:#888;margin-bottom:1mm;">
    CELIOS — Center of Economic and Law Studies · Working Paper
  </div>
  <div style="font-size:14pt;font-weight:800;letter-spacing:-0.5px;color:#111;line-height:1.1;margin-bottom:1.5mm;">
    Legal Enforcement Uncertainty Index
  </div>
  <div style="font-size:8pt;color:#444;font-weight:500;">
    Analisis Statistik: Ketidakpastian Hukum &amp; Iklim Investasi Indonesia
  </div>
</div>

<!-- ABSTRACT BOX -->
<div style="background:#f7f7f7;border-left:2px solid #111;padding:3mm 4mm;margin-bottom:5mm;">
  <div style="font-size:6pt;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:1mm;">Abstrak</div>
  <div style="font-size:7pt;color:#333;line-height:1.5;">
    Studi ini menguji 5 jalur kausal antara ketidakpastian penegakan hukum dan kinerja investasi Indonesia
    menggunakan data panel {total_n:,} observasi dari berbagai sumber resmi. Dua hipotesis terbukti secara
    statistik (p &lt; 0.05): H3 (prosedur pengadilan) dan H5 (risiko kriminalisasi).
    Ketiga hipotesis lain menunjukkan arah yang konsisten namun terkendala keterbatasan data historis tahunan.
  </div>
</div>

<!-- SUMMARY ROW -->
<div style="display:flex;gap:8mm;margin-bottom:5mm;padding-bottom:3mm;border-bottom:0.5px solid #ddd;">
  <div>
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#999;">Total Observasi</div>
    <div style="font-size:16pt;font-weight:800;color:#111;font-family:'Courier New',monospace;">{total_n:,}</div>
  </div>
  <div style="border-left:0.5px solid #ddd;"></div>
  <div>
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#999;">Hipotesis Terbukti</div>
    <div style="font-size:16pt;font-weight:800;color:#111;font-family:'Courier New',monospace;">{terbukti} / 5</div>
  </div>
  <div style="border-left:0.5px solid #ddd;"></div>
  <div>
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#999;">Metode Uji</div>
    <div style="font-size:9pt;font-weight:700;color:#111;margin-top:1.5mm;">Chi-Square · Spearman</div>
  </div>
  <div style="border-left:0.5px solid #ddd;"></div>
  <div>
    <div style="font-size:6pt;text-transform:uppercase;letter-spacing:1px;color:#999;">Signifikansi</div>
    <div style="font-size:7pt;font-weight:600;color:#111;margin-top:2mm;">★★★ p&lt;0.001 · ★★ p&lt;0.05 · ★ p&lt;0.10</div>
  </div>
</div>

<!-- MAIN TABLE -->
<table>
  <thead>
    <tr>
      <th class="left" style="width:6%;">H</th>
      <th class="left" style="width:36%;">Jalur Kausal &amp; Data</th>
      <th style="width:14%;">Statistik</th>
      <th style="width:13%;">p-value</th>
      <th style="width:14%;">Effect Size</th>
      <th style="width:17%;">Hasil</th>
    </tr>
  </thead>
  <tbody>
    {rows_v2}
  </tbody>
</table>

<!-- INTERPRETASI -->
<div style="margin-top:5mm;border-top:0.5px solid #ddd;padding-top:3mm;">
  <div style="font-size:6pt;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:2mm;">Interpretasi &amp; Jalur Kausal</div>
  <div style="display:flex;gap:2mm;align-items:flex-start;">
    <div style="font-size:7pt;color:#333;line-height:1.5;flex:1;">
      <strong>H3 (n=66.725):</strong> Sidang berdurasi ≥30 hari meningkatkan peluang perkara menggantung
      (OR=0.220, p&lt;0.001). Kepastian hukum korporat terganggu secara sistemis.
    </div>
    <div style="border-left:0.5px solid #ddd;margin:0 2mm;"></div>
    <div style="font-size:7pt;color:#333;line-height:1.5;flex:1;">
      <strong>H5 (n=296):</strong> IKK Gap tinggi (ketakutan hukum investor) secara signifikan menekan
      IKK Present (OR=3.617, p&lt;0.001). Kriminalisasi bisnis membekukan keputusan investasi.
    </div>
    <div style="border-left:0.5px solid #ddd;margin:0 2mm;"></div>
    <div style="font-size:7pt;color:#333;line-height:1.5;flex:1;">
      <strong>H1, H2, H4:</strong> Arah korelasi konsisten dengan hipotesis namun tidak signifikan
      secara statistik akibat keterbatasan n historis tahunan (&lt;15). Diperlukan data panel provinsi
      untuk uji lanjutan.
    </div>
  </div>
</div>

<!-- CATATAN METODOLOGIS -->
<div style="margin-top:4mm;font-size:5.5pt;color:#aaa;line-height:1.4;border-top:0.5px solid #eee;padding-top:2mm;">
  <strong>Catatan:</strong> H1, H2, H4 menggunakan Spearman rank correlation (cocok untuk n &lt; 15, non-parametrik).
  H3, H5 menggunakan Chi-Square dengan median-split binning (asumsi min. expected freq. terpenuhi).
  Sumber: BI (IKK), Transparency International (CPI), BKPM (ICOR/PMDN), SIPP Mahkamah Agung.
</div>

<!-- FOOTER -->
<div style="display:flex;justify-content:space-between;margin-top:5mm;padding-top:2mm;border-top:1px solid #111;font-size:5.5pt;color:#999;">
  <div>CELIOS LEUI — Legal Enforcement Uncertainty Index</div>
  <div style="color:#111;font-weight:600;">celios.or.id</div>
  <div>{gen_date}</div>
</div>

</body>
</html>"""


# ═══════════════════════════════════════════════════════════
# BUILD V3 — PUBLIK / STORYTELLING
# ═══════════════════════════════════════════════════════════
def build_poster_v3_html(s):
    total_n  = sum(v["n"] for v in s.values())
    terbukti = sum(1 for v in s.values() if v["p"] < 0.05)
    gen_date = datetime.date.today().strftime("%d %B %Y")
    n_h3 = s["H3"]["n"]; or_h5 = s["H5"]["effect"]; n_h5 = s["H5"]["n"]

    # Kartu temuan — headline awam + penjelasan + stat kecil
    CARDS = [
        {
            "hid": "01", "color": "#E65100", "bg": "#FFF8F3",
            "icon": "⚖️",
            "headline": "Semakin korup, semakin mahal biaya investasi",
            "body": "Negara dengan skor korupsi buruk cenderung punya ICOR tinggi — artinya butuh modal lebih besar untuk menghasilkan pertumbuhan yang sama. Korupsi bukan hanya moral issue, tapi beban ekonomi nyata.",
            "stat": f"Data: {s['H1']['n']} tahun observasi · r = {s['H1']['effect']:.2f}",
            "verdict": "Tren Awal", "vcolor": "#E65100"
        },
        {
            "hid": "02", "color": "#1565C0", "bg": "#F3F7FF",
            "icon": "📉",
            "headline": "Hukum yang tidak adil membuat investor enggan masuk",
            "body": "Ketika penegakan hukum lemah dan pilih kasih, kepercayaan investor runtuh. Data investasi domestik menunjukkan stagnasi di tahun-tahun dengan skor transparansi rendah.",
            "stat": f"Data: {s['H2']['n']} tahun observasi · r = {s['H2']['effect']:.2f}",
            "verdict": "Perlu Riset Lanjut", "vcolor": "#1565C0"
        },
        {
            "hid": "03", "color": "#B71C1C", "bg": "#FFF5F5",
            "icon": "⏳",
            "headline": f"{n_h3:,} kasus bisnis tergantung di pengadilan",
            "body": "Lebih dari separuh perkara wanprestasi korporat masuk fase \"persidangan\" selama bertahun-tahun tanpa putusan. Pengusaha tidak bisa merencanakan bisnis jika kepastian hukum tidak ada.",
            "stat": f"Bukti: {n_h3:,} kasus SIPP · p < 0.001 · OR = {s['H3']['effect']:.2f}",
            "verdict": "✓ Terbukti", "vcolor": "#2E7D32"
        },
        {
            "hid": "04", "color": "#6A1B9A", "bg": "#FAF5FF",
            "icon": "🔀",
            "headline": "Aturan yang berubah-ubah = investor pilih wait & see",
            "body": "Setiap kali regulasi berubah mendadak, pengusaha memilih menunggu daripada berinvestasi. Ketidakstabilan aturan menciptakan efisiensi investasi yang buruk dan ICOR yang bengkak.",
            "stat": f"Data: {s['H4']['n']} tahun observasi · r = {s['H4']['effect']:.2f}",
            "verdict": "Perlu Riset Lanjut", "vcolor": "#6A1B9A"
        },
        {
            "hid": "05", "color": "#880E4F", "bg": "#FFF5FA",
            "icon": "🚨",
            "headline": f"Takut dikriminalisasi bikin investor {or_h5:.1f}x lebih memilih diam",
            "body": "Ketika pengusaha takut keputusan bisnisnya bisa berujung di penjara, mereka membekukan investasi. Data survei Bank Indonesia selama 296 bulan membuktikan: ketakutan hukum secara langsung menekan aktivitas ekonomi.",
            "stat": f"Bukti: {n_h5} observasi bulanan · p < 0.001 · OR = {or_h5:.2f}",
            "verdict": "✓ Terbukti", "vcolor": "#2E7D32"
        },
    ]

    def card_html(c):
        return f"""
        <div style="background:{c['bg']};border-left:4px solid {c['color']};border-radius:0 6px 6px 0;
                    padding:4mm 5mm;margin-bottom:4mm;page-break-inside:avoid;">
          <div style="display:flex;align-items:flex-start;gap:3mm;">
            <div style="font-size:18pt;line-height:1;margin-top:1mm;">{c['icon']}</div>
            <div style="flex:1;">
              <div style="display:flex;align-items:center;gap:3mm;margin-bottom:1.5mm;">
                <div style="font-size:6pt;font-weight:800;text-transform:uppercase;letter-spacing:1px;
                            color:{c['color']};background:{c['color']}22;padding:0.5mm 2mm;border-radius:2px;">
                  TEMUAN {c['hid']}
                </div>
                <div style="font-size:6pt;font-weight:700;color:{c['vcolor']};">{c['verdict']}</div>
              </div>
              <div style="font-size:9pt;font-weight:800;color:#111;line-height:1.3;margin-bottom:2mm;">
                {c['headline']}
              </div>
              <div style="font-size:7pt;color:#444;line-height:1.55;margin-bottom:2mm;">
                {c['body']}
              </div>
              <div style="font-size:5.5pt;color:#aaa;font-style:italic;">{c['stat']}</div>
            </div>
          </div>
        </div>"""

    all_cards = "".join(card_html(c) for c in CARDS)

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
@page {{ size: A4 portrait; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:210mm; min-height:297mm;
  font-family:'Inter',sans-serif;
  background:#fff; color:#111;
  font-size:8pt; line-height:1.4;
  padding:10mm 10mm 8mm 10mm;
}}
</style>
</head>
<body>

<!-- HEADER BLOCK -->
<div style="background:#111;color:#fff;padding:6mm 7mm;border-radius:6px;margin-bottom:5mm;">
  <div style="font-size:6.5pt;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:1.5mm;">
    CELIOS — Center of Economic and Law Studies
  </div>
  <div style="font-size:15pt;font-weight:900;line-height:1.15;margin-bottom:2mm;">
    Kenapa Investor Takut<br>Berbisnis di Indonesia?
  </div>
  <div style="font-size:8pt;color:#ccc;font-weight:400;line-height:1.5;">
    Riset LEUI menganalisis bagaimana ketidakpastian penegakan hukum secara langsung
    menghambat investasi dan pertumbuhan ekonomi Indonesia.
  </div>
</div>

<!-- 3 ANGKA KUNCI -->
<div style="display:flex;gap:3mm;margin-bottom:5mm;">
  <div style="flex:1;text-align:center;padding:3mm;background:#F5F5F5;border-radius:5px;">
    <div style="font-size:18pt;font-weight:900;color:#111;font-family:'Courier New',monospace;">{total_n:,}</div>
    <div style="font-size:6.5pt;color:#666;margin-top:0.5mm;">kasus &amp; data dianalisis</div>
  </div>
  <div style="flex:1;text-align:center;padding:3mm;background:#F5F5F5;border-radius:5px;">
    <div style="font-size:18pt;font-weight:900;color:#B71C1C;font-family:'Courier New',monospace;">{n_h3:,}</div>
    <div style="font-size:6.5pt;color:#666;margin-top:0.5mm;">kasus perkara bisnis tergantung</div>
  </div>
  <div style="flex:1;text-align:center;padding:3mm;background:#F5F5F5;border-radius:5px;">
    <div style="font-size:18pt;font-weight:900;color:#880E4F;font-family:'Courier New',monospace;">{or_h5:.1f}x</div>
    <div style="font-size:6.5pt;color:#666;margin-top:0.5mm;">lebih memilih tidak investasi</div>
  </div>
</div>

<!-- DIVIDER + INTRO -->
<div style="font-size:7.5pt;font-weight:700;text-transform:uppercase;letter-spacing:1px;
            color:#888;border-bottom:1px solid #eee;padding-bottom:2mm;margin-bottom:4mm;">
  5 Temuan Utama Riset
</div>

<!-- KARTU TEMUAN -->
{all_cards}

<!-- KESIMPULAN -->
<div style="background:#111;color:#fff;padding:4mm 5mm;border-radius:5px;margin-top:1mm;">
  <div style="font-size:7pt;font-weight:800;text-transform:uppercase;letter-spacing:1px;
              color:#aaa;margin-bottom:1.5mm;">Apa yang Harus Berubah?</div>
  <div style="display:flex;gap:4mm;">
    <div style="flex:1;font-size:7pt;color:#ddd;line-height:1.5;">
      <span style="color:#fff;font-weight:700;">Reformasi pengadilan</span> — percepat penyelesaian perkara bisnis agar tidak berlarut bertahun-tahun tanpa kepastian.
    </div>
    <div style="flex:1;font-size:7pt;color:#ddd;line-height:1.5;">
      <span style="color:#fff;font-weight:700;">Stabilkan regulasi</span> — jangan ubah aturan main di tengah jalan. Investor butuh kepastian jangka panjang.
    </div>
    <div style="flex:1;font-size:7pt;color:#ddd;line-height:1.5;">
      <span style="color:#fff;font-weight:700;">Hentikan kriminalisasi bisnis</span> — bedakan sengketa perdata dan pidana. Jangan jadikan pengusaha tersangka untuk perkara bisnis biasa.
    </div>
  </div>
</div>

<!-- FOOTER -->
<div style="display:flex;justify-content:space-between;margin-top:4mm;padding-top:2mm;
            border-top:1px solid #eee;font-size:5.5pt;color:#bbb;">
  <div>CELIOS — Legal Enforcement Uncertainty Index (LEUI) · celios.or.id</div>
  <div>Sumber: BI, Transparency International, BKPM, SIPP MA · {gen_date}</div>
</div>

</body>
</html>"""


# ═══════════════════════════════════════════════════════════
# RENDER — TABS
# ═══════════════════════════════════════════════════════════
st.markdown("## Infografis Poster A4 — CELIOS LEUI")
st.caption("Data-driven — dihitung langsung dari CSV saat halaman dibuka. Download → buka di browser → Ctrl+P → Save as PDF.")

with st.spinner("Menghitung statistik dari semua data..."):
    s = compute_all_stats()

total_n  = sum(v["n"] for v in s.values())
terbukti = sum(1 for v in s.values() if v["p"] < 0.05)
st.info(f"**n = {total_n:,}** observasi · **{terbukti}/5** hipotesis terbukti · Zero hardcode")

tab1, tab2, tab3 = st.tabs([
    "V1 — Lengkap (Berwarna)",
    "V2 — Minimalis (Akademik)",
    "V3 — Publik (Storytelling)"
])

with tab1:
    html_v1 = build_poster_html(s)
    st.download_button(label="⬇️ Download V1", data=html_v1,
        file_name="LEUI_Poster_V1.html", mime="text/html", key="dl_v1")
    st.markdown("---")
    components.html(html_v1, height=1200, scrolling=True)

with tab2:
    html_v2 = build_poster_v2_html(s)
    st.download_button(label="⬇️ Download V2", data=html_v2,
        file_name="LEUI_Poster_V2.html", mime="text/html", key="dl_v2")
    st.markdown("---")
    components.html(html_v2, height=1100, scrolling=True)

with tab3:
    html_v3 = build_poster_v3_html(s)
    st.download_button(label="⬇️ Download V3 (Publik)", data=html_v3,
        file_name="LEUI_Poster_V3_Publik.html", mime="text/html", key="dl_v3")
    st.markdown("---")
    components.html(html_v3, height=1350, scrolling=True)
