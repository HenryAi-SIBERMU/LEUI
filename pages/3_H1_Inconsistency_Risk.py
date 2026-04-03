"""
Page 1 — H1: Inconsistency Risk
Analisis inkonsistensi biaya/realisasi investasi antar wilayah sebagai proxy
ketidakpastian hukum daerah.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

st.set_page_config(
    page_title="H1: Inconsistency Risk — CELIOS LEUI",
    page_icon="ref/Celios China-Indonesia Energy Transition.png",
    layout="wide"
)
render_sidebar()

# ── Styles ──
st.markdown("""
<style>
.metric-card {
    background: #1E1E1E;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #4CAF50;
}
.metric-label {
    font-size: 0.9rem;
    color: #AAA;
    margin-bottom: 5px;
}
.metric-delta {
    font-size: 0.8rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Color palette ──
C_PRIMARY = "#43A047"
C_ACCENT = "#66BB6A"
C_WARN = "#FF9800"
C_DANGER = "#E53935"
C_BG_CARD = "#1E1E1E"

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_COLORS_ASING = "#42A5F5"
PLOTLY_COLORS_DOMESTIK = "#66BB6A"


# ── Helper: Gini coefficient ──
def gini_coefficient(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    arr = arr[arr >= 0]
    if len(arr) < 2 or arr.sum() == 0:
        return np.nan
    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr))


# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "processed")

@st.cache_data
def load_data():
    df_asing = pd.read_csv(os.path.join(DATA, "realisasi_investasi_asing.csv"), parse_dates=["date"])
    df_domestik = pd.read_csv(os.path.join(DATA, "realisasi_investasi_domestik.csv"), parse_dates=["date"])
    df_icor = pd.read_csv(os.path.join(DATA, "icor_nasional.csv"), parse_dates=["date"])
    return df_asing, df_domestik, df_icor

df_asing, df_domestik, df_icor = load_data()

# Pre-calculate stats for narrative
n_prov_asing = df_asing['provinsi'].nunique()
n_kab_asing = df_asing['kabupaten'].nunique()
n_prov_domestik = df_domestik['provinsi'].nunique()
n_kab_domestik = df_domestik['kabupaten'].nunique()
date_range_start = df_asing['date'].min().strftime('%Y')
date_range_end = df_asing['date'].max().strftime('%Y')


# ══════════════════════════════════════════════════════════════
# HEADER (mengikuti format EBT PODES)
# ══════════════════════════════════════════════════════════════
st.title(_("H1: Inconsistency Risk — Ketidakkonsistenan Hukum Antar Wilayah"))
subtitle = _("Analisis Distribusi & Ketimpangan Investasi (Proxy Inkonsistensi Lingkungan Usaha)")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology Expander ──
with st.expander(_("ℹ️ Metodologi: Analisis Inconsistency Risk (H1)"), expanded=False):
    st.markdown(_("""
    **Metode Analisis:** Halaman ini mengukur tingkat inkonsistensi lingkungan usaha/hukum antar wilayah
    menggunakan proxy ekonomi — distribusi realisasi investasi antar provinsi.

    **1. Standard Deviation per Kuartal:**
    *   Mengukur volatilitas/sebaran investasi antar provinsi untuk setiap kuartal.
    *   Formula: `SD = sqrt(Σ(xi - μ)² / N)` dimana xi = investasi provinsi i, μ = rata-rata.
    *   SD tinggi → investasi sangat tidak merata → indikasi lingkungan usaha inkonsisten antar daerah.

    **2. Gini Coefficient per Kuartal:**
    *   Mengukur ketimpangan distribusi investasi (0 = merata sempurna, 1 = sangat timpang).
    *   Gini > 0.4 dianggap ketimpangan moderat-tinggi.
    *   Diaplikasikan ke realisasi investasi per provinsi, bukan ICOR (karena ICOR hanya data nasional).

    **3. Distribusi per Provinsi (Top/Bottom):**
    *   Rata-rata investasi (PMA + PMDN) per provinsi, disajikan sebagai bar chart horizontal.
    *   Rasio Top/Bottom = indikasi kesenjangan extremitas.

    **4. ICOR Nasional:**
    *   Incremental Capital-Output Ratio: investasi yang dibutuhkan untuk 1 unit pertumbuhan PDB.
    *   ICOR naik → efisiensi investasi menurun → salah satu penyebab: ketidakpastian hukum.
    """))

# ── Intro Narrative + Sumber ──
intro_text = _("""Data realisasi investasi mencakup **{n_prov} provinsi** dan **{n_kab}+ kabupaten/kota**
selama periode **{start}–{end}** (kuartalan). Analisis ini memetakan sejauh mana investasi
terdistribusi secara merata antar daerah. Ketimpangan yang tinggi mengindikasikan bahwa beberapa
wilayah memiliki lingkungan hukum/usaha yang jauh lebih kondusif dibanding wilayah lain —
sebuah proxy dari *inconsistency risk* dalam penegakan hukum.""")

sumber_text = _("Data dari <code>realisasi_investasi_asing.csv</code> ({n_row_a} baris, {n_prov_a} provinsi), "
                "<code>realisasi_investasi_domestik.csv</code> ({n_row_d} baris, {n_prov_d} provinsi), "
                "dan <code>icor_nasional.csv</code> ({n_row_i} baris). Sumber asli: CEIC/BKPM & BPS.")

st.markdown(
    intro_text.format(n_prov=n_prov_asing, n_kab=n_kab_asing, start=date_range_start, end=date_range_end) +
    f"\n\n<small>📁 <b>Sumber:</b> {sumber_text.format(n_row_a=len(df_asing), n_prov_a=n_prov_asing, n_row_d=len(df_domestik), n_prov_d=n_prov_domestik, n_row_i=len(df_icor))}</small>",
    unsafe_allow_html=True
)
st.caption(_("📊 Visualisasi: Empat panel analisis — (1) Volatilitas Std. Deviation, (2) Gini Coefficient, (3) Distribusi Top/Bottom Provinsi, (4) Tren ICOR Nasional. Semua dihitung dari agregasi level kabupaten ke provinsi per kuartal."))


# ══════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════
# Pre-calc KPI values
def calc_std_per_quarter(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    std_q = prov_q.groupby("date")["nilai_idr_bn"].std().reset_index()
    std_q.columns = ["date", "std_dev"]
    std_q["tipe"] = label
    return std_q

def calc_gini_per_quarter(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    gini_q = prov_q.groupby("date")["nilai_idr_bn"].apply(gini_coefficient).reset_index()
    gini_q.columns = ["date", "gini"]
    gini_q["tipe"] = label
    return gini_q

std_asing = calc_std_per_quarter(df_asing, "Investasi Asing (PMA)")
std_domestik = calc_std_per_quarter(df_domestik, "Investasi Domestik (PMDN)")
gini_asing = calc_gini_per_quarter(df_asing, "Investasi Asing (PMA)")
gini_domestik = calc_gini_per_quarter(df_domestik, "Investasi Domestik (PMDN)")

latest_std_a = std_asing["std_dev"].iloc[-1] if len(std_asing) > 0 else 0
latest_std_d = std_domestik["std_dev"].iloc[-1] if len(std_domestik) > 0 else 0
latest_gini_a = gini_asing["gini"].dropna().iloc[-1] if len(gini_asing.dropna()) > 0 else 0
latest_gini_d = gini_domestik["gini"].dropna().iloc[-1] if len(gini_domestik.dropna()) > 0 else 0
latest_icor_d = df_icor["icor_pmdn"].iloc[-1] if len(df_icor) > 0 else 0
latest_icor_a = df_icor["icor_pma"].iloc[-1] if len(df_icor) > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gini PMA (Terakhir)</div>
        <div class="metric-value">{latest_gini_a:.3f}</div>
        <div class="metric-delta" style="color: {'#EF5350' if latest_gini_a > 0.4 else '#4CAF50'}">{'Timpang' if latest_gini_a > 0.4 else 'Moderat'}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gini PMDN (Terakhir)</div>
        <div class="metric-value">{latest_gini_d:.3f}</div>
        <div class="metric-delta" style="color: {'#EF5350' if latest_gini_d > 0.4 else '#4CAF50'}">{'Timpang' if latest_gini_d > 0.4 else 'Moderat'}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Std. Dev PMA (Terakhir)</div>
        <div class="metric-value">{latest_std_a:,.1f}</div>
        <div class="metric-delta" style="color: #AAA">IDR Bn</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ICOR PMA (Terakhir)</div>
        <div class="metric-value">{latest_icor_a:.2f}</div>
        <div class="metric-delta" style="color: #AAA">Rasio efisiensi</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 1. STD DEVIATION PER KUARTAL
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.1 Volatilitas Investasi Antar Provinsi (Std. Deviation)"))

std_desc = _("""Grafik di bawah menunjukkan **standar deviasi** realisasi investasi antar provinsi per kuartal.
Semakin tinggi nilai SD, semakin **timpang** sebaran investasi antar daerah — artinya beberapa provinsi
menerima investasi jauh lebih besar dibanding yang lain. Perhatikan apakah tren SD meningkat dari waktu ke waktu,
yang akan mengindikasikan kesenjangan yang makin melebar.""")
std_src = _("Agregasi <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code> — di-groupby provinsi per kuartal, dihitung SD.")
st.markdown(f"{std_desc}\n\n<small>📁 <b>Sumber:</b> {std_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Line chart — Std. Deviation realisasi investasi antar provinsi per kuartal, terpisah untuk PMA (biru) dan PMDN (hijau). Metode: groupby(kuartal, provinsi) → sum → std per kuartal."))

std_combined = pd.concat([std_asing, std_domestik], ignore_index=True)

fig_std = px.line(
    std_combined, x="date", y="std_dev", color="tipe",
    color_discrete_map={
        "Investasi Asing (PMA)": PLOTLY_COLORS_ASING,
        "Investasi Domestik (PMDN)": PLOTLY_COLORS_DOMESTIK
    },
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "std_dev": "Std. Deviation (IDR Bn)", "tipe": "Tipe Investasi"}
)
fig_std.update_layout(
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20),
    hovermode="x unified"
)
st.plotly_chart(fig_std, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# 2. GINI COEFFICIENT PER KUARTAL
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.2 Ketimpangan Distribusi Investasi (Gini Coefficient)"))

gini_desc = _("""Gini Coefficient mengukur ketimpangan distribusi investasi antar provinsi.
Nilai **0** = merata sempurna, **1** = sangat timpang (semua investasi terkonsentrasi di satu provinsi).
Garis putus-putus kuning pada **0.4** menandai batas ketimpangan moderat. Jika Gini secara konsisten
berada di atas 0.4, ini mengindikasikan bahwa investasi **sangat terkonsentrasi** di beberapa provinsi saja —
sebuah cerminan bahwa lingkungan usaha/hukum antar daerah **tidak konsisten**.""")
gini_src = _("Agregasi per provinsi per kuartal dari <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code>.")
st.markdown(f"{gini_desc}\n\n<small>📁 <b>Sumber:</b> {gini_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Line chart — Gini Coefficient per kuartal untuk PMA dan PMDN. Garis threshold 0.4 menandai batas ketimpangan moderat. Metode: sum investasi per provinsi → hitung Gini Lorenz per kuartal."))

gini_combined = pd.concat([gini_asing, gini_domestik], ignore_index=True)

fig_gini = px.line(
    gini_combined, x="date", y="gini", color="tipe",
    color_discrete_map={
        "Investasi Asing (PMA)": PLOTLY_COLORS_ASING,
        "Investasi Domestik (PMDN)": PLOTLY_COLORS_DOMESTIK
    },
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "gini": "Gini Coefficient", "tipe": "Tipe Investasi"}
)
fig_gini.update_layout(
    height=420,
    yaxis=dict(range=[0, 1]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20),
    hovermode="x unified"
)
fig_gini.add_hline(y=0.4, line_dash="dash", line_color=C_WARN, annotation_text="Batas ketimpangan moderat (0.4)")
st.plotly_chart(fig_gini, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# 3. DISTRIBUSI PER PROVINSI — TOP/BOTTOM
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.3 Distribusi Investasi per Provinsi"))

prov_desc = _("""Grafik di bawah menampilkan rata-rata realisasi investasi (PMA + PMDN) per kuartal,
dikelompokkan berdasarkan provinsi. Perhatikan **rasio ketimpangan** antara provinsi teratas dan terbawah:
jika rasio ini sangat besar, ini memperkuat argumen bahwa lingkungan usaha antar daerah sangat tidak merata.""")
prov_src = _("Gabungan <code>realisasi_investasi_asing.csv</code> + <code>realisasi_investasi_domestik.csv</code>, di-groupby provinsi → mean per kuartal.")
st.markdown(f"{prov_desc}\n\n<small>📁 <b>Sumber:</b> {prov_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Bar chart horizontal — Top 15 dan Bottom 15 provinsi berdasarkan rata-rata investasi. Warna menunjukkan besaran nilai. Metode: mean(nilai_idr_bn) per provinsi dari gabungan PMA+PMDN."))

df_all = pd.concat([
    df_asing.assign(tipe="Asing"),
    df_domestik.assign(tipe="Domestik")
], ignore_index=True)

prov_avg = df_all.groupby("provinsi")["nilai_idr_bn"].mean().sort_values(ascending=True).reset_index()
prov_avg.columns = ["provinsi", "rata_rata_idr_bn"]

n_show = 15
tab_top, tab_bottom = st.tabs([_("Top 15 Provinsi"), _("Bottom 15 Provinsi")])

with tab_top:
    top = prov_avg.tail(n_show)
    fig_top = px.bar(
        top, x="rata_rata_idr_bn", y="provinsi", orientation="h",
        color="rata_rata_idr_bn",
        color_continuous_scale=["#1B5E20", "#43A047", "#A5D6A7"],
        template=PLOTLY_TEMPLATE,
        labels={"rata_rata_idr_bn": "Rata-rata (IDR Bn/kuartal)", "provinsi": ""}
    )
    fig_top.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20), showlegend=False,
                          coloraxis_showscale=False)
    st.plotly_chart(fig_top, use_container_width=True)

with tab_bottom:
    bottom = prov_avg.head(n_show)
    fig_bottom = px.bar(
        bottom, x="rata_rata_idr_bn", y="provinsi", orientation="h",
        color="rata_rata_idr_bn",
        color_continuous_scale=["#B71C1C", "#E53935", "#EF9A9A"],
        template=PLOTLY_TEMPLATE,
        labels={"rata_rata_idr_bn": "Rata-rata (IDR Bn/kuartal)", "provinsi": ""}
    )
    fig_bottom.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20), showlegend=False,
                             coloraxis_showscale=False)
    st.plotly_chart(fig_bottom, use_container_width=True)

# Rasio ketimpangan
if len(prov_avg) > 1:
    top_val = prov_avg["rata_rata_idr_bn"].iloc[-1]
    bot_val = prov_avg["rata_rata_idr_bn"].iloc[0]
    ratio = top_val / bot_val if bot_val > 0 else 0
    st.markdown(f"""
    <div style="background:{C_BG_CARD}; padding:14px 20px; border-radius:10px;
                border-left:5px solid {C_WARN}; margin-top:10px;">
        <strong>Rasio Ketimpangan:</strong> Provinsi teratas menerima investasi
        <span style="color:{C_WARN}; font-size:1.3rem; font-weight:700;">{ratio:,.0f}x</span>
        lebih besar dari provinsi terbawah ({prov_avg.iloc[-1]['provinsi']} vs {prov_avg.iloc[0]['provinsi']}).
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 4. ICOR NASIONAL TREND
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.4 Tren ICOR Nasional (Efisiensi Investasi)"))

icor_desc = _("""ICOR (Incremental Capital-Output Ratio) mengukur efisiensi investasi di level nasional.
ICOR **tinggi** berarti Indonesia membutuhkan **lebih banyak investasi** untuk menghasilkan 1 unit pertumbuhan PDB.
Tren ICOR yang naik mengindikasikan lingkungan investasi yang makin tidak efisien — salah satu penyebabnya
adalah **ketidakpastian hukum** yang meningkatkan biaya-biaya tersembunyi (legal fees, delays, risk premium).""")
icor_src = _("Data dari <code>icor_nasional.csv</code> (15 baris tahunan, 2010-2024). Sumber asli: BPS.")
st.markdown(f"{icor_desc}\n\n<small>📁 <b>Sumber:</b> {icor_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Line chart — ICOR PMDN (hijau) dan ICOR PMA (biru) per tahun. Metode: data langsung dari icor_nasional.csv tanpa transformasi."))

fig_icor = go.Figure()
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pmdn"],
    mode="lines+markers", name="ICOR PMDN",
    line=dict(color=PLOTLY_COLORS_DOMESTIK, width=2.5),
    marker=dict(size=7)
))
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pma"],
    mode="lines+markers", name="ICOR PMA",
    line=dict(color=PLOTLY_COLORS_ASING, width=2.5),
    marker=dict(size=7)
))
fig_icor.update_layout(
    template=PLOTLY_TEMPLATE,
    height=400,
    yaxis_title="ICOR (Rasio)",
    xaxis_title="Tahun",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20),
    hovermode="x unified"
)
st.plotly_chart(fig_icor, use_container_width=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(_("ICOR PMDN (Terakhir)"), f"{latest_icor_d:.2f}")
with col2:
    st.metric(_("ICOR PMA (Terakhir)"), f"{latest_icor_a:.2f}")
with col3:
    avg_icor = (latest_icor_d + latest_icor_a) / 2 if latest_icor_a else latest_icor_d
    st.metric(_("Rata-rata ICOR"), f"{avg_icor:.2f}")


# ══════════════════════════════════════════════════════════════
# FOOTER — Interpretasi
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("Interpretasi & Temuan Utama"))

st.markdown(f"""
**Analisis Temuan Utama:**
- **Gini Coefficient tinggi (>0.4)** menunjukkan investasi sangat terkonsentrasi
  di beberapa provinsi saja — mencerminkan lingkungan hukum/usaha yang tidak merata.
- **Std. Deviation yang meningkat** menandakan semakin besarnya kesenjangan
  investasi antar daerah dari waktu ke waktu.
- **ICOR yang naik** mengindikasikan efisiensi investasi menurun — biaya untuk
  menghasilkan pertumbuhan ekonomi semakin mahal, salah satunya didorong oleh ketidakpastian hukum.
- **Rasio ketimpangan** antar provinsi yang sangat besar memperkuat argumen bahwa
  penegakan hukum dan kebijakan investasi **tidak konsisten** antar daerah.

<small><em>Catatan: Data ini menggunakan proxy ekonomi. Analisis ideal membutuhkan
data putusan pengadilan dan variansi vonis untuk mengukur inkonsistensi hukum secara langsung.</em></small>
""", unsafe_allow_html=True)
