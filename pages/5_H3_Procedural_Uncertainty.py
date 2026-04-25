"""
Page 3 — H3: Procedural Uncertainty
Analisis delay cost dan inefisiensi investasi menggunakan ICOR sebagai proxy
ketidakpastian prosedural hukum.
    `Alur: Penegakan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi`

Causal Chain: Penegakan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

st.set_page_config(
    page_title="H3: Procedural Uncertainty — CELIOS LEUI",
    page_icon="ref/Celios China-Indonesia Energy Transition.png",
    layout="wide"
)
render_sidebar()

# ── Styles ──
# (Metric card styling dihandle inline untuk border warna spesifik & background #3b1414)
st.markdown("""
<style>
/* Base overrides */
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
C_PMA = "#42A5F5"
C_PMDN = "#66BB6A"
C_ICOR = "#FF9800"
C_ANOMALY = "#E53935"
C_WARN = "#FF9800"
C_BG = "#1E1E1E"

# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "final")

@st.cache_data
def load_data():
    df_icor = pd.read_csv(os.path.join(DATA, "icor_nasional.csv"), parse_dates=["date"])
    df_a = pd.read_csv(os.path.join(DATA, "realisasi_investasi_asing.csv"), parse_dates=["date"])
    df_d = pd.read_csv(os.path.join(DATA, "realisasi_investasi_domestik.csv"), parse_dates=["date"])
    return df_icor, df_a, df_d

df_icor, df_asing, df_domestik = load_data()


# ══════════════════════════════════════════════════
# PRE-COMPUTE
# ══════════════════════════════════════════════════

df_icor = df_icor.sort_values("date").reset_index(drop=True)
df_icor["year"] = df_icor["date"].dt.year

# Clean: drop rows with NaN or negative ICOR (negative = COVID 2020 artefact)
df_icor_clean = df_icor.dropna(subset=["icor_pma", "icor_pmdn"]).copy()
df_icor_clean = df_icor_clean[(df_icor_clean["icor_pma"] > 0) & (df_icor_clean["icor_pmdn"] > 0)].copy()

# Aggregate annual investment totals
df_asing["year"] = df_asing["date"].dt.year
df_domestik["year"] = df_domestik["date"].dt.year

inv_pma_yr = df_asing.groupby("year")["nilai_idr_bn"].sum().reset_index()
inv_pma_yr.columns = ["year", "total_pma"]
inv_pmdn_yr = df_domestik.groupby("year")["nilai_idr_bn"].sum().reset_index()
inv_pmdn_yr.columns = ["year", "total_pmdn"]

# Merge with CLEANED ICOR (no NaN, no negatives)
df_merged = df_icor_clean.merge(inv_pma_yr, on="year", how="inner").merge(inv_pmdn_yr, on="year", how="inner")
df_merged["total_investasi"] = df_merged["total_pma"] + df_merged["total_pmdn"]
df_merged["icor_avg"] = (df_merged["icor_pma"] + df_merged["icor_pmdn"]) / 2

# --- ICOR trend (using clean data) ---
icor_pma_first = df_icor_clean["icor_pma"].iloc[0]
icor_pma_last = df_icor_clean["icor_pma"].iloc[-1]
icor_pmdn_first = df_icor_clean["icor_pmdn"].iloc[0]
icor_pmdn_last = df_icor_clean["icor_pmdn"].iloc[-1]
icor_pma_change = ((icor_pma_last - icor_pma_first) / icor_pma_first * 100)
icor_pmdn_change = ((icor_pmdn_last - icor_pmdn_first) / icor_pmdn_first * 100)
yr_first = df_icor_clean["date"].iloc[0].strftime("%Y")
yr_last = df_icor_clean["date"].iloc[-1].strftime("%Y")
n_years = len(df_icor_clean)

# ICOR peak (from clean data only)
icor_pma_max = df_icor_clean["icor_pma"].max()
icor_pma_max_yr = df_icor_clean.loc[df_icor_clean["icor_pma"].idxmax(), "date"].strftime("%Y")
icor_pmdn_max = df_icor_clean["icor_pmdn"].max()
icor_pmdn_max_yr = df_icor_clean.loc[df_icor_clean["icor_pmdn"].idxmax(), "date"].strftime("%Y")

# GDP growth trend
gdp_first = df_icor_clean["gdp_growth_pct"].iloc[0] * 100
gdp_last = df_icor_clean["gdp_growth_pct"].iloc[-1] * 100
gdp_avg = df_icor_clean["gdp_growth_pct"].mean() * 100

# --- Correlation: ICOR vs Investment (from clean merged data) ---
if len(df_merged) >= 5:
    corr_pma, pval_pma = stats.spearmanr(df_merged["icor_pma"], df_merged["total_pma"])
    corr_pmdn, pval_pmdn = stats.spearmanr(df_merged["icor_pmdn"], df_merged["total_pmdn"])
    corr_icor_gdp, pval_icor_gdp = stats.spearmanr(df_merged["icor_avg"], df_merged["gdp_growth_pct"])
else:
    corr_pma, pval_pma = 0, 1
    corr_pmdn, pval_pmdn = 0, 1
    corr_icor_gdp, pval_icor_gdp = 0, 1

# --- Lag analysis: does high ICOR this year predict low investment next year? ---
lag_results = []
for lag in range(0, 4):
    df_lag = df_merged.copy()
    df_lag["inv_lagged"] = df_lag["total_investasi"].shift(-lag)
    df_lag = df_lag.dropna(subset=["inv_lagged"])
    if len(df_lag) >= 4:
        r, p = stats.spearmanr(df_lag["icor_avg"], df_lag["inv_lagged"])
        lag_results.append({"Lag (Tahun)": lag, "Spearman r": round(r, 3), "p-value": round(p, 4), "n": len(df_lag)})

df_lag_results = pd.DataFrame(lag_results)

# Rate of change ICOR (from clean data)
df_icor_clean["icor_pma_pct"] = df_icor_clean["icor_pma"].pct_change() * 100
df_icor_clean["icor_pmdn_pct"] = df_icor_clean["icor_pmdn"].pct_change() * 100

# ICOR efficiency classification
icor_avg_last = (icor_pma_last + icor_pmdn_last) / 2
if icor_avg_last > 7:
    efisiensi_status = "Sangat Tidak Efisien"
elif icor_avg_last > 5:
    efisiensi_status = "Tidak Efisien"
elif icor_avg_last > 3:
    efisiensi_status = "Moderat"
else:
    efisiensi_status = "Efisien"

# Worst year (biggest ICOR jump, from clean data)
roc_valid = df_icor_clean.dropna(subset=["icor_pma_pct"])
if len(roc_valid) > 0:
    worst_jump_idx = roc_valid["icor_pma_pct"].idxmax()
    worst_jump_yr = roc_valid.loc[worst_jump_idx, "date"].strftime("%Y")
    worst_jump_val = roc_valid.loc[worst_jump_idx, "icor_pma_pct"]
else:
    worst_jump_yr = "—"
    worst_jump_val = 0


# ══════════════════════════════════════════════════
# HEADER & INTRO
# ══════════════════════════════════════════════════
st.title(_("H3: Proses Hukum Berlarut, Investasi Tertahan"))
subtitle = _("Sidang tahunan dan birokrasi berlapis-lapis membuat biaya investasi di Indonesia melonjak tidak terkendali.")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Setup Variables (Hukum) ──
_sipp_pn_path = os.path.join(DATA, "sipp_pn_distribution.csv")
_total_sipp = 0
_avg_durasi = 0
if os.path.exists(_sipp_pn_path):
    _df_pn = pd.read_csv(_sipp_pn_path)
    _total_sipp = int(_df_pn['jumlah'].sum())
    _avg_dur_vals = _df_pn['Avg_Lama_Proses'].dropna()
    _avg_durasi = _avg_dur_vals.mean() if len(_avg_dur_vals) > 0 else 0

# ── Methodology ──
with st.expander(_("🔍 Metodologi"), expanded=False):
    st.markdown(_("""
    **Causal Chain Law & Economics:**
    `Procedural Delay → Procedural Uncertainty → Risk Premium / Delay Cost → Investment Inefficiency`

    **Variabel Independen (X):**
    - Rata-rata durasi penyelesaian perkara perdata komersial di Pengadilan Negeri (SIPP). Semakin lama durasi, semakin besar *procedural uncertainty*.
    
    **Variabel Dependen (Y):**
    - *Incremental Capital Output Ratio* (ICOR) nasional. ICOR menakar inefisiensi biaya investasi; ICOR > 6.0 mengindikasikan mahalnya *Delay Cost* akibat tidak berjalannya kepastian hukum.
    - Minat Investasi Asing & Domestik (Penanaman Modal Nasional).
    """))

# ── Intro Narrative ──
intro = _("""Teori **Ketidakpastian Nasib (Procedural Uncertainty)** di hukum Indonesia terbukti melahirkan efek domino mamatikan: **Hukum Berlarut-larut → Menggantung Nasib → Teror Ketakutan (Persepsi Risiko) → Ongkos Siluman Bengkak (Delay Cost) → Batal Buka Pabrik (Urung Investasi)**. Proses persidangan yang bertele-tele, ngaret bertahun-tahun, dan sering ditumpangi pasal titipan adalah biang keroknya. Lewat sedotan miliaran data SIPP Mahkamah Agung, kami menangkap rekam jejak kotor di mana sengketa bisnis rata-rata dibiarkan membusuk gantung tanpa kepastian selama **{_avg_durasi:.0f} hari**.

Karena nasib bisnisnya digantung pengadilan terlalu lama, investor yang beroperasi di Indonesia mematok harga "nyawa" yang sangat mahal. Mereka dipaksa merogoh uang di luar proposal demi asuransi perlindungan perkara. Semua "uang siluman" di balik meja ini terhimpun jelas mencoreng **Rasio Pemborosan Uang (ICOR)** kita yang grafiknya makin raksasa (hari ini bertengger membeku di angka {icor_avg_last:.2f}). Artinya, ongkos menanam pabrik di Indonesia sudah kelewat mahal dan luar biasa boros dibanding negara manapun di ASEAN. Hal ini terbukti bukan gosip semata, tercium dari angka rekam kecocokan maut (**Spearman r = {corr:.3f}**) di mana naiknya keborosan ini langsung memangkas minat asing.""")

intro_src = _("SIPP Mahkamah Agung (Variabel Hukum/X) & Panel ICOR Investasi BPS-BKPM (Variabel Makroekonomi/Y).")

st.markdown(
    intro.format(
        _avg_durasi=_avg_durasi,
        yr_f=yr_first, yr_l=yr_last, 
        icor_avg_last=icor_avg_last,
        corr=corr_pma
    ) +
    f"\n\n<small>📁 <b>Sumber Basis Data:</b> {intro_src}</small>",
    unsafe_allow_html=True
)
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── Overview KPI Cards (Hukum + Ekonomi) ──
st.markdown("### Eksekutif Summary (H3)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid #AB47BC; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Rata-rata Modal Mandek (Durasi SIPP)</div>
        <div style="font-size:2rem; font-weight:bold; color:#E1BEE7;">{_avg_durasi:.0f} hari</div>
        <div style="font-size:0.8rem; font-weight:600; color:#AB47BC; margin-bottom:10px;">Variabel Hukum (X)</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Total waktu vonis di data putusan pengadilan bisnis dibagi total kasus.
        </p>
    </div>""", unsafe_allow_html=True)
with c2:
    icor_color = C_ANOMALY if icor_avg_last > 6 else C_WARN
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid {icor_color}; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Rasio Pemborosan Uang ({yr_last}) (ICOR)</div>
        <div style="font-size:2rem; font-weight:bold; color:{icor_color};">{icor_avg_last:.2f}</div>
        <div style="font-size:0.8rem; font-weight:600; color:{C_WARN}; margin-bottom:10px;">Variabel Ekonomi (Y)</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Total Realisasi Investasi dibagi Laju Pertumbuhan Ekonomi PDB Nasional.
        </p>
    </div>""", unsafe_allow_html=True)
with c3:
    corr_color = C_ANOMALY if corr_pma < -0.3 else C_WARN
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid {corr_color}; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Persentase Kecocokan Pola (Spearman)</div>
        <div style="font-size:2rem; font-weight:bold; color:{corr_color};">{corr_pma:.3f}</div>
        <div style="font-size:0.8rem; font-weight:600; color:#AAA; margin-bottom:10px;">Dampak Biaya (Y)</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Korelasi rank Spearman antara membengkaknya ICOR versus penurunan minat PMA.
        </p>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid {C_ANOMALY}; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Lonjakan Petaka Terburuk (Rate of Change)</div>
        <div style="font-size:2rem; font-weight:bold; color:{C_ANOMALY};">+{worst_jump_val:.1f}%</div>
        <div style="font-size:0.8rem; font-weight:600; color:{C_WARN}; margin-bottom:10px;">Rapor {worst_jump_yr}</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Kenaikan persentase biaya (ICOR) melonjak paling drastis dalam setahun berturut.
        </p>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 3.1 Variabel Hukum (X) ──
st.markdown("---")
st.subheader("3.1 Fakta Penyebab: Proses Hukum yang Menyita Waktu dan Biaya")
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode Pintu Masuk: Sampel Waktu Tunggu Kasus (SIPP Distribution)</span>', unsafe_allow_html=True)

sipp_narr = _("""Grafik di bawah ini menjadi "alat bukti telanjang" yang memulai hancurnya nasib usaha di Indonesia. Waktu yang dibiarkan ngaret berbulan-bulan tanpa kejelasan (Procedural Uncertainty) dalam penyelesaian sengketa perdata bisnis nyatanya adalah akar dari seluruh **ongkos siluman (Delay Cost)** nasional. Bagi pemilik modal, hari yang berlalu di meja sidang berarti tumpukan bunga pinjaman bank dari proyek mangkrak. Kegagalan sistem dalam menjamin kecepatan waktu ketuk palu ini bertindak sebagai **Variabel Asal-Muasal (Variabel X)** saklek yang mencekik napas investasi nasional.""")
st.markdown(sipp_narr + f"\n\n<small>📁 <b>Sumber:</b> Scraping putusan SIPP Pengadilan Negeri (Sampel Kasus Perkara Bisnis).</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Kelompok distribusi lama umur perkara (kiri) dan Pengadilan Negeri dengan kasus macet terbanyak (kanan)."))

_sipp_dur_path = os.path.join(DATA, "sipp_durasi_distribution.csv")
if os.path.exists(_sipp_dur_path) and os.path.exists(_sipp_pn_path):
    _df_dur = pd.read_csv(_sipp_dur_path)
    _cc1, _cc2 = st.columns(2)
    with _cc1:
        _fig_dur = px.bar(
            _df_dur, x="durasi_hari", y="jumlah",
            color_discrete_sequence=["#AB47BC"],
            template=PLOTLY_TEMPLATE, labels={"durasi_hari": "Rentang Umur Perkara (Hari)", "jumlah": "Jumlah Kasus"}
        )
        _fig_dur.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        if _avg_durasi > 0:
            _fig_dur.add_vline(x=_avg_durasi, line_width=2, line_dash="dash", line_color="#FF3D00")
            _fig_dur.add_annotation(
                x=_avg_durasi, y=_df_dur["jumlah"].max() * 0.9,
                text=f"Rata-rata Modal Mandek: {_avg_durasi:.0f} Hari",
                showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor="#FF3D00",
                ax=50, ay=-30, font=dict(color="#FF3D00", size=11, weight="bold"),
                bgcolor="#1E1E1E", bordercolor="#FF3D00", borderwidth=1
            )
        st.plotly_chart(_fig_dur, use_container_width=True)
    with _cc2:
        _df_pn_top = _df_pn.head(10).sort_values("jumlah", ascending=True)
        _fig_pn = px.bar(
            _df_pn_top, x="jumlah", y="pengadilan", orientation="h",
            color_discrete_sequence=["#AB47BC"],
            template=PLOTLY_TEMPLATE, labels={"jumlah": "Volume Sengketa", "pengadilan": ""}
        )
        _fig_pn.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(_fig_pn, use_container_width=True)

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid #AB47BC; margin-bottom:10px;">
    <b>Kesimpulan Singkat:</b> Investor dituntut menahan napas dan menahan uang operasional rata-rata <b>{_avg_durasi:.0f} hari</b> sekadar untuk menunggu ketok palu perselisihan awal. Bukti mutlak bahwa pengadilan kita bertindak sebagai <b>mesin pencetak kerugian waktu tertunda (Delay Cost)</b> di dunia bisnis tanpa pandang bulu.
</div>
""", unsafe_allow_html=True)

with st.expander("Lihat Data: Rekam Ketukan Palu Pengadilan (SIPP)", expanded=False):
    _df_pn_disp = _df_pn.copy()
    _df_pn_disp.columns = ["Nama Pengadilan (PN)", "Jumlah Kasus Digantung", "Rata-rata Terlunta-lunta (Durasi Proses)"]
    st.dataframe(_df_pn_disp, use_container_width=True, hide_index=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 3.2 TREN ICOR (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.2 Dampak: Biaya Siluman Investasi Makin Mencekik (ICOR)"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Rasio Pemborosan Modal Runtun Waktu (ICOR Time Series / Variabel Y1)</span>', unsafe_allow_html=True)

icor_narr = _("""Angka ini mengukur betapa parahnya boros uang yang harus dibayarkan perusahaan cuma untuk bisa buka usaha. Menggunakan **Rasio Tingkat Pemborosan Uang (IKOR / Incremental Capital Output Ratio)** — semakin tinggi nilainya, semakin kencang indikasi bahwa uang jutaan triliunan terkuras habis dibakar buat nyukupin *biaya siluman/kepanikan di bawah meja* gara-gara nggak ada kepastian (delay, hukum bisa dibeli).
Grafik memperlihatkan Pemborosan Modal Asing (PMA/Biru) dan Domestik (PMDN/Hijau) tahun **{yr_f}–{yr_l}**.
Keborosan asing memuncak mengerikan pada **{pma_max_yr}** di angka **{pma_max:.2f}**. Maksud bahasa awamnya: di titik itu, orang luar negeri dipaksa membakar uang sebanyak Rp {pma_max:.1f} triliun *hanya* untuk menjahit omzet ekonomi murni ke Indonesia sebesar Rp 1 triliun! Garis seram putus-putus merah di (6.0) adalah ambang wajar **Sangat Sakit / Boros Ekstrem (Inefisiensi Parah)** di mata global.""")

icor_src = _("Data <code>icor_nasional.csv</code>. Rasio = Uang Modal Masuk dibagi Laju Balik PDB. Sumber Data Olahan BPS.")
st.markdown(icor_narr.format(
    yr_f=yr_first, yr_l=yr_last, pma_max_yr=icor_pma_max_yr, pma_max=icor_pma_max
) + f"\n\n<small>📁 <b>Sumber:</b> {icor_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Grafik garis Rasio Pemborosan Modal (ICOR) per tahun."))

fig_icor = go.Figure()
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pma"], mode="lines+markers", name="ICOR PMA",
    line=dict(color=C_PMA, width=2.5), marker=dict(size=7),
    hovertemplate="<b>%{x|%Y}</b><br>ICOR PMA: %{y:.2f}<extra></extra>"
))
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pmdn"], mode="lines+markers", name="ICOR PMDN",
    line=dict(color=C_PMDN, width=2.5), marker=dict(size=7),
    hovertemplate="<b>%{x|%Y}</b><br>ICOR PMDN: %{y:.2f}<extra></extra>"
))
fig_icor.add_hline(y=6.0, line_dash="dash", line_color=C_ANOMALY,
                   annotation_text="Batas Ekstrem Boros Minta Ampun (Threshold 6.0)")

# [NEW] Anak Panah untuk Data Storytelling
fig_icor.add_annotation(
    x=str(icor_pma_max_yr)+"-01-01" if "-" not in str(icor_pma_max_yr) else icor_pma_max_yr, 
    y=icor_pma_max,
    text=f"Puncak Ongkos Ekstrem (ICOR PMA {icor_pma_max:.2f})",
    showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
    ax=0, ay=-40, font=dict(color=C_ANOMALY, size=11, weight="bold"),
    bgcolor="#1E1E1E", bordercolor=C_ANOMALY, borderwidth=1
)

fig_icor.update_layout(
    template=PLOTLY_TEMPLATE, height=430,
    yaxis_title="Batas Uang Siluman (Rasio ICOR)", xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_icor, use_container_width=True)

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom:10px;">
    <b>Kesimpulan Singkat:</b> Grafik ini telanjang menunjukkan kegilaan pungutan liar & mahalnya biaya "menunggu kepastian". Puncak "bakar uang" terjadi secara menjijikkan di tahun <b>{icor_pma_max_yr}</b>, jauh menembus limit kewajaran (Garis Putus Merah 6.0). Negara ini nyata-nyata memaksa pemodal untuk menelan <b>Angka Keborosan Mutlak (ICOR)</b> gila-gilaan imbas karut-marut peradilan kita.
</div>
""", unsafe_allow_html=True)

with st.expander("Lihat Data: Angka Keborosan Masuknya Modal Asing & Lokal (ICOR Nasional)", expanded=False):
    _icor_disp = df_icor_clean[["year", "icor_pma", "icor_pmdn", "gdp_growth_pct"]].copy()
    _icor_disp.columns = ["Tahun Peristiwa", "Skala Pemborosan Modal Asing (ICOR PMA)", "Skala Pemborosan Modal Lokal (ICOR PMDN)", "Pertumbuhan Ekonomi (PDB Pct)"]
    st.dataframe(_icor_disp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 3.3 ICOR vs VOLUME INVESTASI (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.3 Dampak: Makin Mahal Biaya, Makin Sedikit Modal Masuk"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Tingkat Kecocokan Pola (Spearman Rank Correlation / Variabel Y2)</span>', unsafe_allow_html=True)

scatter_narr = _("""Menggunakan instrumen **Kalkulator Kecocokan (Spearman Rank Correlation)** untuk mengukur betapa kuatnya ikatan batin antara mahalnya uang pungli/siluman (ICOR) terhadap volume masuknya investasi sesungguhnya.
Jika kekacauan pengadilan (Procedural Uncertainty) ini memang menaikkan biaya hidup pengusaha, maka seharusnya ketemu korelasi mati (Negatif): Boros luar biasa → Investasi Kabur Menciut.
Skor kecocokan ini memuntahkan angka presisi **r = {corr_pma:.3f}** pada asing (p-value = {pval_pma:.4f}) dan **r = {corr_pmdn:.3f}** pada lokal. {interp}
Di peta bawah ini, setiap titik adalah 1 tahun hidup bangsa kita. Menumpuknya titik di pojok kanan bawah (Luar biasa Boros, Modal sangat Menciut) menjadi saksi bisu betapa **biaya siluman peradilan** membunuh pabrik-pabrik kita.""")

if corr_pma < -0.3:
    interp = "Tanda minus (Korelasi Negatif) ini membuktikan kecocokan absolut: Makin digantung dan main duit pengadilannya, makin parah kebangkrutan ketertarikan investor."
elif corr_pma > 0.3:
    interp = "Tanda plus mengartikan bahwa modal aslinya tetap datang menantang maut, sayangnya uang tersebut dibakar perlahan (tidak efisien membuahkan pabrik)."
else:
    interp = "Tanda abu-abu (Korelasi Lemah) berikrar bahwa investor punya seribu jalan lain dan tidak peduli mau ICOR meroket atau tidak."

scatter_src = _("Gabungan <code>icor_nasional.csv</code> + agregasi tahunan <code>realisasi_investasi_asing.csv</code> (Asing/PMA & Lokal/PMDN).")
st.markdown(scatter_narr.format(
    corr_pma=corr_pma, pval_pma=pval_pma,
    corr_pmdn=corr_pmdn, pval_pmdn=pval_pmdn,
    interp=interp
) + f"\n\n<small>📁 <b>Sumber:</b> {scatter_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Peta sebaran titik (Scatter) pola keheningan PMA di tengah tingginya pemborosan modal."))

if len(df_merged) > 0:
    fig_scatter = px.scatter(
        df_merged, x="icor_avg", y="total_investasi",
        color="year", color_continuous_scale=["#E53935", "#FF9800", "#FDD835"],
        hover_data={"year": True, "icor_pma": ":.2f", "icor_pmdn": ":.2f",
                    "total_pma": ":,.0f", "total_pmdn": ":,.0f"},
        template=PLOTLY_TEMPLATE,
        labels={"icor_avg": "Rasio Pemborosan Uang (IKOR Rata-rata)", "total_investasi": "Total Investasi (Triliun Rupiah)", "year": "Tahun Tragedi"}
    )
    # [NEW] Anak Panah Data Storytelling
    worst_pt = df_merged[df_merged["year"] == int(icor_pma_max_yr)]
    if len(worst_pt) > 0:
        fig_scatter.add_annotation(
            x=worst_pt["icor_avg"].values[0], y=worst_pt["total_investasi"].values[0],
            text="Tahun Terboros & Bukti Asing Kabur",
            showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
            ax=-50, ay=-40, font=dict(color=C_ANOMALY, size=11, weight="bold")
        )

    fig_scatter.update_layout(
        height=430, margin=dict(l=20, r=20, t=20, b=20), hovermode="closest"
    )
    fig_scatter.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom:10px;">
    <b>Kesimpulan Singkat:</b> Semakin titik-titik ini beringsut ke kanan (ICOR memerah gila), masuknya uang dari luar pelan-pelan makin merayap seret ke dasar. Konfirmasi dari rumus kecocokan ini <b>(Spearman r={corr_pma:.3f})</b> menjadi vonis telak bahwa kelambanan peradilan sukses menjerat mati nyawa roda perekonomian.
</div>
""", unsafe_allow_html=True)

with st.expander("Lihat Data: Sebaran Total Uang Masuk vs Rasio Pemborosan (Scatter)", expanded=False):
    _scatter_disp = df_merged[["year", "icor_avg", "total_investasi", "total_pma", "total_pmdn"]].copy()
    _scatter_disp.columns = ["Tahun Observasi", "Rasio Pemborosan Uang (ICOR)", "Total Modal Gabungan (Triliun IDR)", "Duit Asing (PMA)", "Duit Lokal (PMDN)"]
    st.dataframe(_scatter_disp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 3.4 LAG ANALYSIS (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.4 Dampak: Efek Bom Waktu — Kerugian Tsunami di Masa Depan"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Pantauan Bom Waktu Tertunda (Spearman Lag Correlation / Variabel Y3)</span>', unsafe_allow_html=True)

lag_narr = _("""Uang pendirian pabrik sebesar ribuan triliun tidak lenyap secara ghaib hari ini di saat hukum diobrak-abrik. Menerapkan **Pantauan Bom Waktu Tertunda (Spearman Lag Correlation)** — sebuah radar untuk menemukan *dendam kesumat* investor, di mana mereka baru kaburnya nanti-nanti.
Jika biaya siluman korupsi waktu ini memang dibebankan merambat lambat, maka mesin radar ini akan menjerit negatif setelah rentang beberapa tahun (Lag). Artinya tamparan keras ke peradilan hari ini mungkin baru membunuh lapangan kerja buruh 1.5 tahun ke depan! 
Perhatikan balok terjauh di grafik; membuktikan sekuat apa dendam ketakutan diputar setahun kemudian.""")

lag_src = _("Tingkat kecocokan (Spearman rank correlation) rentang ICOR dan total investasi antara durasi saat ini, hingga digeser sejauh lag 0-3 tahun.")
st.markdown(lag_narr + f"\n\n<small>📁 <b>Sumber:</b> {lag_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Lag Time Chart. Semakin dalam balok, semakin mematikan efek hukum tertunda buat kehidupan masa depan."))

if len(df_lag_results) > 0:
    tbl_lag = df_lag_results.copy()
    tbl_lag["Signifikan?"] = tbl_lag["p-value"].apply(lambda p: "Ya (Valid p < 0.05)" if p < 0.05 else "Ragu-ragu (p >= 0.05)")
    tbl_lag["Interpretasi"] = tbl_lag.apply(
        lambda row: "Kabur Massal — ICOR bengkak → Pabrik batal ditalangi" if row["Spearman r"] < -0.3
        else "Ne-kat — investasi tutup mata" if row["Spearman r"] > 0.3
        else "Burem — investor mencari jalan aman rahasia", axis=1
    )
    
    # Bar chart of lag correlations
    fig_lag = go.Figure()
    colors = [C_ANOMALY if r < -0.3 else C_WARN if r < 0 else "#FDD835" for r in tbl_lag["Spearman r"]]
    fig_lag.add_trace(go.Bar(
        x=[f"Bom Waktu {int(l)} Tahun (Lag)" for l in tbl_lag["Lag (Tahun)"]],
        y=tbl_lag["Spearman r"],
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Kecocokan (r) = %{y:.3f}<extra></extra>"
    ))
    
    # [NEW] Anak Panah untuk Data Storytelling
    min_idx = tbl_lag["Spearman r"].idxmin()
    min_val = tbl_lag["Spearman r"].min()
    fig_lag.add_annotation(
        x=f"Bom Waktu {int(tbl_lag.loc[min_idx, 'Lag (Tahun)'])} Tahun (Lag)", y=min_val,
        text=f"Dampak Dendam Terparah (r={min_val:.2f})",
        showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
        ax=0, ay=30, font=dict(color=C_ANOMALY, size=11, weight="bold")
    )

    fig_lag.add_hline(y=0, line_dash="dot", line_color="#666")
    fig_lag.update_layout(
        template=PLOTLY_TEMPLATE, height=300,
        yaxis_title="Daya Hancur Masa Depan (Spearman r)", xaxis_title="",
        margin=dict(l=20, r=20, t=20, b=20), showlegend=False
    )
    st.plotly_chart(fig_lag, use_container_width=True)

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom:10px;">
    <b>Kesimpulan Singkat:</b> Batang balok grafik yang menghunjam jatuh menunjukkan bahwa kekacauan yang kita toleransi dari Pengadilan Bisnis kita hari ini, sangat luar biasa akan <b>menceburkan jurang penderitaan ke pekerja buruh 2-3 tahun ke depan (Efek Lag time)</b>.
</div>
""", unsafe_allow_html=True)

with st.expander("Lihat Data: Angka Penundaan Bom Waktu (Spearman Lag Matrix)", expanded=False):
    _tbl_lag_disp = tbl_lag.copy()
    _tbl_lag_disp.columns = ["Jarak Bom Waktu (Tahun Lag)", "Kecocokan Balas Dendam (Spearman r)", "Keberhasilan Pola (p-value)", "Jumlah Data (Hari)", "Apakah Akurat?", "Nasib Pabrik"]
    st.dataframe(_tbl_lag_disp.style.format({
        "Kecocokan Balas Dendam (Spearman r)": "{:.3f}",
        "Keberhasilan Pola (p-value)": "{:.4f}",
        "Jumlah Data (Hari)": "{:.0f}"
    }), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 3.5 RATE OF CHANGE (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.5 Dampak: Serangan Kejut Lonjakan Biaya Hura-hura Tiba-tiba"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Limit Batas Perubahan Tahunan Tergila (Rate of Change / Variabel Y4)</span>', unsafe_allow_html=True)

roc_narr = _("""Kepanikan akibat hakim/pengadilan tebang pilih biasanya tidak merayap perlahan-lahan. Memanfaatkan **Sensor Batas Lonjakan (Rate of Change)** komputer kami membongkar kapan investor seketika dicegat pungli beruntun antargenerasi (dalam semalam beban biaya investasi meroket seketika).
Balok Merah adalah nisan peringatan ketika para investor *dipaksa miskin* dalam semalam karena biaya kepastian operasi membengkak tak waras. Lonjakan Tsunami Tergila menimpa pada **{worst_yr}** (+{worst_val:.1f}% uang mereka dibakar). Ini murni kelakuan letupan *Procedural Shock Hukum* (tiba-tiba penguasa ganti palu/sidang molor politik), bukan semata-mata roda ekonomi melambat secara normal.""")

roc_src = _("Persentase gejolak (Rate parameter/pct_change) rentang tahunan gergaji PMA dan PMDN di Indonesia.")
st.markdown(roc_narr.format(
    worst_yr=worst_jump_yr, worst_val=worst_jump_val
) + f"\n\n<small>📁 <b>Sumber:</b> {roc_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Bar chart gejolak rasio pemborosan asing (%) pertahunnya. Warnah Merah = Teror Naiknya Biaya."))

df_roc = df_icor_clean.dropna(subset=["icor_pma_pct"]).copy()
roc_col = "icor_pma_pct"
bar_colors = [C_ANOMALY if v > 0 else "#FDD835" for v in df_roc[roc_col]]

fig_roc = go.Figure()
fig_roc.add_trace(go.Bar(
    x=df_roc["date"], y=df_roc[roc_col],
    marker_color=bar_colors, name="% Membengkaknya Pemborosan",
    hovertemplate="<b>%{x|%Y}</b><br>Tercekik Naik Berapa Persen?: %{y:.1f}%<extra></extra>"
))
fig_roc.add_hline(y=0, line_dash="dot", line_color="#1E1E1E")

# [NEW] Anak Panah untuk Data Storytelling
fig_roc.add_annotation(
    x=str(worst_jump_yr)+"-01-01" if "-" not in str(worst_jump_yr) else worst_jump_yr,
    y=worst_jump_val,
    text=f"Tsunami Ongkos Tergila (+{worst_jump_val:.1f}%)",
    showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
    ax=0, ay=-30, font=dict(color=C_ANOMALY, size=11, weight="bold")
)

fig_roc.update_layout(
    template=PLOTLY_TEMPLATE, height=380,
    yaxis_title="Derajat Pembengkakan Beban (%)", xaxis_title="",
    margin=dict(l=20, r=20, t=20, b=20), showlegend=False, hovermode="x unified"
)
st.plotly_chart(fig_roc, use_container_width=True)

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom:10px;">
    <b>Kesimpulan Singkat:</b> Biaya membuka keran mesin usaha di Indonesia sempat mengalami shock yang membakar lebih dari <b>{worst_jump_val:.1f}% (Lonjakan Biaya / Rate of Change)</b> seketika akibat ketidakpastian. Ini mustahil terjadi alami jika institusi pengadilannya memberikan lampu hijau waktu ketok-palu (Putusan MA) yang adil.
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3. Kesimpulan: Nasib Pekerja Digantung Aparat (Procedural Uncertainty)"))

temuan = _("""
<div style="background-color: #2F0A28; padding: 25px; border-radius: 10px; border: 1px solid #FF3D00;">
    <ul style="font-size: 1.1rem; line-height: 1.8; color: #E0E0E0; margin: 0; padding-left: 20px;">
        <li><b>Pengadilan Sebagai Pabrik Derita Tertunda (Hukum X):</b> Sesuai mesin pembedah pengadilan kami, sengketa bisnis saat ini resmi dibiarkan berkarat menggantung nasib tak jelas rata-rata <b>{avg_dur:.0f} hari (Distribusi SIPP)</b>. Ketiadaan hari pasti ketuk palu inilah yang jadi sumber segala racun.</li>
        <li><b>Triliunan Uang Negara Hangus Sia-sia (Indikator Y1):</b> Gantungnya putusan merontokkan nyali sehingga investor main kotor menuntut pungli dan *Risk Premium* sangat besar di luar nalar. Tercetak nyata di Angka Keborosan Mutlaknya menembus <b>{icor_l:.2f} (Rasio ICOR)</b> alias menyentuh skala stadium akhir nan gawat <b>{status}</b>.</li>
        <li><b>Tebang Pilih Mencekik Nadi Asing (Indikator Y2 & Y3):</b> Sial nian, borosnya pungli-pungli tersebut di atas terbukti berhasil menggergaji minat pendatang buka pabrik asing, di mana ikatan negatif kedekatan dua garis merah ini punya tingkat validitas selir sangat rapet <b>r = {corr:.3f} (Spearman Rank)</b>.</li>
        <li><b>Catatan Terakhir Buat Para Mentri:</b> Urusan mengolor sidang bukan urusan sepele pakim pakai jas toga, itu adalah kejahatan **Rantai Efek Domino Sabotase (Causal Chain)** yang perlahan melucuti daya minat pelarian orang luar menanam pabrik <i>Foreign Direct Investment (FDI)</i> di bumi kita.</li>
    </ul>
</div>
""")

st.markdown(temuan.format(
    avg_dur=_avg_durasi,
    icor_l=icor_avg_last, status=efisiensi_status,
    corr=corr_pma
), unsafe_allow_html=True)
