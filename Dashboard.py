import streamlit as st
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

# --- Page Config ---
st.set_page_config(
    page_title="Dashboard LEUI — CELIOS",
    page_icon="ref/Celios China-Indonesia Energy Transition.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', sans-serif; }

.main-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #43A047, #66BB6A, #81C784);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    line-height: 1.2;
}

.sub-title {
    font-size: 1.1rem;
    color: #9E9E9E;
    font-weight: 300;
    margin-top: 0;
    margin-bottom: 2rem;
}

.org-badge {
    display: inline-block;
    background: linear-gradient(135deg, #1B5E20, #2E7D32);
    color: white;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.stat-card {
    background: linear-gradient(135deg, #1A1F2B, #232B3B);
    border: 1px solid #2E7D3233;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.stat-card:hover {
    transform: translateY(-2px);
    border-color: #43A047;
}
.stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    color: #66BB6A;
    margin: 8px 0;
}
.stat-label {
    font-size: 0.85rem;
    color: #9E9E9E;
    font-weight: 400;
}
.stat-sub {
    font-size: 0.75rem;
    color: #616161;
    margin-top: 4px;
}

.nav-card {
    background: linear-gradient(135deg, #1A1F2B, #232B3B);
    border: 1px solid #ffffff11;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.nav-card:hover { border-color: #43A047; }
.nav-icon { font-size: 1.6rem; margin-bottom: 8px; }
.nav-title { font-size: 1rem; font-weight: 600; color: #E0E0E0; }
.nav-desc { font-size: 0.8rem; color: #757575; margin-top: 4px; }

.footer {
    text-align: center;
    color: #616161;
    font-size: 0.75rem;
    margin-top: 4rem;
    padding: 2rem 0;
    border-top: 1px solid #ffffff0a;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
render_sidebar()

# --- Header ---
st.markdown('<div class="org-badge">CELIOS — Center of Economic and Law Studies</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Legal Enforcement Uncertainty Index</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Dashboard Analisis Risk Pricing Investasi Indonesia — Penegakan Hukum → Ketidakpastian → Risiko Ekonomi</div>', unsafe_allow_html=True)

# --- Helper Functions & Imports for Charts ---
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

PLOTLY_TEMPLATE = "plotly_dark"

def gini_coefficient(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    arr = arr[arr >= 0]
    if len(arr) < 2 or arr.sum() == 0: return np.nan
    arr = np.sort(arr)
    n = len(arr)
    idx = np.arange(1, n + 1)
    return (2 * np.sum(idx * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr))

# --- Dashboard Layout: Executive Summary ---
st.markdown("---")
st.markdown("## 1. H1: Inconsistency Risk — Kesenjangan Distribusi Investasi")
st.markdown("Ketimpangan distribusi PMDN (Hijau) & PMA (Biru) melampaui batas moderat (Gini > 0.4), indikasi awal hukum tak bisa diprediksi secara merata lintas wilayah.")

# Load H1 Data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")
df_asing = pd.read_csv(os.path.join(DATA_DIR, "realisasi_investasi_asing.csv"), parse_dates=["date"])
df_dom = pd.read_csv(os.path.join(DATA_DIR, "realisasi_investasi_domestik.csv"), parse_dates=["date"])

def calc_gini_q(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    g = prov_q.groupby("date")["nilai_idr_bn"].apply(gini_coefficient).reset_index()
    g.columns = ["date", "gini"]
    g["tipe"] = label
    return g

gini_a = calc_gini_q(df_asing, "Investasi Asing (PMA)")
gini_d = calc_gini_q(df_dom, "Investasi Domestik (PMDN)")
gini_combined = pd.concat([gini_a, gini_d], ignore_index=True)

fig_h1 = px.line(
    gini_combined, x="date", y="gini", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": "#42A5F5", "Investasi Domestik (PMDN)": "#66BB6A"},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "gini": "Gini Coefficient", "tipe": "Tipe Investasi"}
)
fig_h1.update_layout(
    height=400, yaxis=dict(range=[0, 1]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified"
)
fig_h1.add_hline(y=0.4, line_dash="dash", line_color="#FF9800", annotation_text="Batas Moderat (0.4)")
st.plotly_chart(fig_h1, use_container_width=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# --- H2: Selective Enforcement ---
st.markdown("---")
st.markdown("## 2. H2: Selective Enforcement — Anomali Kepercayaan Konsumen")
st.markdown("Deteksi anomali pada Indeks Kepercayaan Konsumen (IKK) Ekspektasi. Titik merah (Z-Score < -2) menandakan *crash* ekspektasi yang tiba-tiba dan di luar kewajaran fluktuasi ekonomi.")

df_ikk = pd.read_csv(os.path.join(DATA_DIR, "ikk_expect_vs_present.csv"), parse_dates=["date"]).sort_values("date").reset_index(drop=True)
df_ikk["ikk_exp_pct"] = df_ikk["ikk_expectation"].pct_change() * 100
exp_mean = df_ikk["ikk_exp_pct"].mean()
exp_std = df_ikk["ikk_exp_pct"].std()
df_ikk["ikk_exp_zscore"] = (df_ikk["ikk_exp_pct"] - exp_mean) / exp_std
df_ikk["is_exp_anomaly"] = df_ikk["ikk_exp_zscore"] < -2

fig_h2 = go.Figure()
fig_h2.add_trace(go.Scatter(
    x=df_ikk["date"], y=df_ikk["ikk_expectation"], mode="lines", name="IKK Ekspektasi", line=dict(color="#42A5F5", width=2)
))
fig_h2.add_trace(go.Scatter(
    x=df_ikk["date"], y=df_ikk["ikk_present"], mode="lines", name="IKK Present", line=dict(color="#66BB6A", width=2)
))
anomalies_h2 = df_ikk[df_ikk["is_exp_anomaly"]]
fig_h2.add_trace(go.Scatter(
    x=anomalies_h2["date"], y=anomalies_h2["ikk_expectation"], mode="markers", name="Anomali (Z < -2)",
    marker=dict(color="#E53935", size=10, symbol="x", line=dict(width=2, color="white")),
    hovertemplate="<b>%{x|%B %Y}</b><br>IKK Ekspektasi: %{y:.1f}<br>Drop: %{customdata[0]:.1f}%<br>Z-Score: %{customdata[1]:.2f}<extra></extra>",
    customdata=anomalies_h2[["ikk_exp_pct", "ikk_exp_zscore"]].values
))
fig_h2.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified"
)
st.plotly_chart(fig_h2, use_container_width=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# --- H4: Regulatory Reversal ---
st.markdown("---")
st.markdown("## 4. H4: Regulatory Reversal — Pelarian Modal Mendadak")
st.markdown("Capital Outflow (Net Sell Obligasi) sebagai *proxy* fear investor terhadap *stranded asset*. Batas oranye menandakan anomali pelarian modal ekstrim (>2 Standar Deviasi).")

df_outflow = pd.read_csv(os.path.join(DATA_DIR, "capital_outflow.csv"), parse_dates=["date"]).sort_values("date").reset_index(drop=True)
mean_ns = df_outflow["net_sell_idr_tn"].mean()
std_ns = df_outflow["net_sell_idr_tn"].std()
df_outflow["z_score"] = (df_outflow["net_sell_idr_tn"] - mean_ns) / std_ns
df_outflow["Color"] = df_outflow["z_score"].apply(lambda z: "#E53935" if z > 2 else "#42A5F5")

fig_h4 = px.bar(
    df_outflow, x="date", y="net_sell_idr_tn", 
    template=PLOTLY_TEMPLATE,
    labels={"date": "Tanggal", "net_sell_idr_tn": "Net Sell (IDR Tn)"}
)
fig_h4.update_traces(marker_color=df_outflow["Color"])
fig_h4.update_layout(
    height=400, margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified"
)
if mean_ns + 2*std_ns < df_outflow["net_sell_idr_tn"].max():
    fig_h4.add_hline(y=mean_ns + 2*std_ns, line_dash="dash", line_color="#FF9800", annotation_text="Batas Anomali (Z>2)")
st.plotly_chart(fig_h4, use_container_width=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# --- H5: Criminalization Risk ---
st.markdown("---")
st.markdown("## 5. H5: Criminalization Risk — Gap Harapan vs Kenyataan")
st.markdown("Mendeteksi pelebaran gap (selisih) ekstrem antara IKK Ekspektasi vs Kondisi Saat Ini. Gap tajam yang disertai *crash* ekspektasi mendadak menandakan episode kepanikan publik.")

df_ikk_h5 = df_ikk.copy()
gap_mean = df_ikk_h5["ikk_gap"].mean()
df_ikk_h5["gap_z"] = (df_ikk_h5["ikk_gap"] - gap_mean) / df_ikk_h5["ikk_gap"].std()
df_ikk_h5["exp_change"] = df_ikk_h5["ikk_expectation"].diff()
df_ikk_h5["exp_crash_z"] = (df_ikk_h5["exp_change"] - df_ikk_h5["exp_change"].mean()) / df_ikk_h5["exp_change"].std()
df_ikk_h5["is_crisis"] = (df_ikk_h5["exp_crash_z"] < -1.5) | (df_ikk_h5["gap_z"] > 2)

fig_h5 = go.Figure()
fig_h5.add_trace(go.Bar(
    x=df_ikk_h5["date"], y=df_ikk_h5["ikk_gap"], name="Lebar Gap IKK", marker_color="#FF9800"
))
anomalies_h5 = df_ikk_h5[df_ikk_h5["is_crisis"]]
fig_h5.add_trace(go.Scatter(
    x=anomalies_h5["date"], y=anomalies_h5["ikk_gap"], mode="markers", name="Episode Krisis",
    marker=dict(color="#E53935", size=10, symbol="x", line=dict(width=2, color="white"))
))
fig_h5.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified",
    yaxis_title="Gap (Poin)"
)
fig_h5.add_hline(y=gap_mean, line_dash="solid", line_color="white", opacity=0.3, annotation_text="Gap Rata-rata")
st.plotly_chart(fig_h5, use_container_width=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div class="footer">
    CELIOS — Center of Economic and Law Studies | Legal Enforcement Uncertainty Index (LEUI) | 2026
</div>
""", unsafe_allow_html=True)
