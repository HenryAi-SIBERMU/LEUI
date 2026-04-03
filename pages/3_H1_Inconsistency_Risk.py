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

# ── Color palette ──
C_PRIMARY = "#43A047"
C_ACCENT = "#66BB6A"
C_WARN = "#FF9800"
C_DANGER = "#E53935"
C_BG_CARD = "#1E1E1E"
C_BORDER = "#2E7D32"

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_COLORS_ASING = "#42A5F5"
PLOTLY_COLORS_DOMESTIK = "#66BB6A"


# ── Helper: Gini coefficient ──
def gini_coefficient(values):
    """Calculate Gini coefficient for a list of non-negative values."""
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


# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
st.title(_("H1: Inconsistency Risk"))
st.markdown(f"""
<div style="background:{C_BG_CARD}; padding:18px 22px; border-radius:12px;
            border-left:5px solid {C_DANGER}; margin-bottom:28px;">
    <h4 style="margin:0 0 8px 0; color:{C_DANGER};">Hipotesis</h4>
    <p style="margin:0; font-size:1.05rem; line-height:1.6;">
        Ketidakkonsistenan penegakan hukum antar wilayah, sektor, dan waktu
        meningkatkan ketidakpastian investasi.<br>
        <strong>Proxy:</strong> Variansi dan ketimpangan realisasi investasi
        antar provinsi sebagai cerminan <em>inkonsistensi lingkungan usaha</em>
        antar daerah.
    </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 1. STD DEVIATION PER KUARTAL
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1. Volatilitas Investasi Antar Provinsi (Std. Deviation)"))
st.caption(_(
    "Standar deviasi realisasi investasi antar provinsi per kuartal. "
    "Semakin tinggi → semakin timpang/inkonsisten distribusi investasi antar daerah."
))

# Aggregate per province per quarter
def calc_std_per_quarter(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    std_q = prov_q.groupby("date")["nilai_idr_bn"].std().reset_index()
    std_q.columns = ["date", "std_dev"]
    std_q["tipe"] = label
    return std_q

std_asing = calc_std_per_quarter(df_asing, "Investasi Asing (PMA)")
std_domestik = calc_std_per_quarter(df_domestik, "Investasi Domestik (PMDN)")
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

# Insight card
latest_std_a = std_asing["std_dev"].iloc[-1] if len(std_asing) > 0 else 0
latest_std_d = std_domestik["std_dev"].iloc[-1] if len(std_domestik) > 0 else 0
col1, col2 = st.columns(2)
with col1:
    st.metric(_("Std. Dev Asing (Kuartal Terakhir)"), f"{latest_std_a:,.2f} IDR Bn")
with col2:
    st.metric(_("Std. Dev Domestik (Kuartal Terakhir)"), f"{latest_std_d:,.2f} IDR Bn")


# ══════════════════════════════════════════════════════════════
# 2. GINI COEFFICIENT PER KUARTAL
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2. Ketimpangan Distribusi Investasi (Gini Coefficient)"))
st.caption(_(
    "Gini Coefficient mengukur ketimpangan distribusi investasi antar provinsi. "
    "0 = merata sempurna, 1 = sangat timpang. Gini tinggi → investasi hanya terkonsentrasi di beberapa daerah."
))

def calc_gini_per_quarter(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    gini_q = prov_q.groupby("date")["nilai_idr_bn"].apply(gini_coefficient).reset_index()
    gini_q.columns = ["date", "gini"]
    gini_q["tipe"] = label
    return gini_q

gini_asing = calc_gini_per_quarter(df_asing, "Investasi Asing (PMA)")
gini_domestik = calc_gini_per_quarter(df_domestik, "Investasi Domestik (PMDN)")
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
# Threshold annotation
fig_gini.add_hline(y=0.4, line_dash="dash", line_color=C_WARN, annotation_text="Batas ketimpangan moderat (0.4)")
st.plotly_chart(fig_gini, use_container_width=True)

# Insight
latest_gini_a = gini_asing["gini"].dropna().iloc[-1] if len(gini_asing.dropna()) > 0 else 0
latest_gini_d = gini_domestik["gini"].dropna().iloc[-1] if len(gini_domestik.dropna()) > 0 else 0
col1, col2 = st.columns(2)
with col1:
    st.metric(_("Gini Asing (Terakhir)"), f"{latest_gini_a:.3f}")
with col2:
    st.metric(_("Gini Domestik (Terakhir)"), f"{latest_gini_d:.3f}")


# ══════════════════════════════════════════════════════════════
# 3. HEATMAP PROVINSI — TOP/BOTTOM
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3. Distribusi Investasi per Provinsi"))
st.caption(_(
    "Rata-rata realisasi investasi (PMA + PMDN) per kuartal, dikelompokkan berdasarkan provinsi. "
    "Ketimpangan antar provinsi mencerminkan inkonsistensi daya saing lingkungan usaha daerah."
))

# Combine asing + domestik
df_all = pd.concat([
    df_asing.assign(tipe="Asing"),
    df_domestik.assign(tipe="Domestik")
], ignore_index=True)

prov_avg = df_all.groupby("provinsi")["nilai_idr_bn"].mean().sort_values(ascending=True).reset_index()
prov_avg.columns = ["provinsi", "rata_rata_idr_bn"]

# Split top/bottom
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

# Ratio
if len(prov_avg) > 1:
    ratio = prov_avg["rata_rata_idr_bn"].iloc[-1] / prov_avg["rata_rata_idr_bn"].iloc[0] if prov_avg["rata_rata_idr_bn"].iloc[0] > 0 else 0
    st.markdown(f"""
    <div style="background:{C_BG_CARD}; padding:14px 20px; border-radius:10px;
                border-left:5px solid {C_WARN}; margin-top:10px;">
        <strong>Rasio Ketimpangan:</strong> Provinsi teratas menerima investasi
        <span style="color:{C_WARN}; font-size:1.3rem; font-weight:700;">{ratio:,.0f}x</span>
        lebih besar dari provinsi terbawah.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 4. ICOR NASIONAL TREND
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("4. Tren ICOR Nasional (Efisiensi Investasi)"))
st.caption(_(
    "ICOR (Incremental Capital-Output Ratio) mengukur efisiensi investasi. "
    "ICOR tinggi → butuh lebih banyak investasi untuk menghasilkan 1 unit pertumbuhan PDB. "
    "Tren naik mengindikasikan lingkungan investasi yang makin tidak efisien."
))

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

# ICOR metrics
col1, col2, col3 = st.columns(3)
with col1:
    latest_icor_d = df_icor["icor_pmdn"].iloc[-1] if len(df_icor) > 0 else 0
    st.metric(_("ICOR PMDN (Terakhir)"), f"{latest_icor_d:.2f}")
with col2:
    latest_icor_a = df_icor["icor_pma"].iloc[-1] if len(df_icor) > 0 else 0
    st.metric(_("ICOR PMA (Terakhir)"), f"{latest_icor_a:.2f}")
with col3:
    avg_icor = (latest_icor_d + latest_icor_a) / 2 if latest_icor_a else latest_icor_d
    st.metric(_("Rata-rata ICOR"), f"{avg_icor:.2f}")


# ══════════════════════════════════════════════════════════════
# FOOTER — Narasi Penutup
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="background:{C_BG_CARD}; padding:18px 22px; border-radius:12px;
            border-left:5px solid {C_PRIMARY}; margin-top:10px;">
    <h4 style="margin:0 0 8px 0; color:{C_ACCENT};">Interpretasi</h4>
    <ul style="line-height:1.8; margin:0;">
        <li><strong>Gini Coefficient tinggi (>0.4)</strong> menunjukkan investasi sangat terkonsentrasi
            di beberapa provinsi saja — mencerminkan lingkungan hukum/usaha yang tidak merata.</li>
        <li><strong>Std. Deviation yang meningkat</strong> menandakan semakin besarnya kesenjangan
            investasi antar daerah dari waktu ke waktu.</li>
        <li><strong>ICOR yang naik</strong> mengindikasikan efisiensi investasi menurun — biaya untuk
            menghasilkan pertumbuhan ekonomi semakin mahal, salah satunya didorong oleh ketidakpastian hukum.</li>
    </ul>
    <p style="margin-top:12px; color:#999; font-size:0.9rem;">
        <em>Catatan: Data ini menggunakan proxy ekonomi. Analisis ideal membutuhkan
        data putusan pengadilan dan variansi vonis untuk mengukur inkonsistensi hukum secara langsung.</em>
    </p>
</div>
""", unsafe_allow_html=True)
