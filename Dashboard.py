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
    page_title="Dashboard Executive Summary — CELIOS LEUI",
    page_icon="ref/Celios China-Indonesia Energy Transition.png",
    layout="wide"
)

render_sidebar()

# ── MODE PENGEMBANGAN (BANNER ONLY) ──
st.warning("### 🚧 Mode Pengembangan 🚧\n\nHalaman **Dashboard Executive Summary** saat ini sedang dalam tahap *maintenance* dan sinkronisasi data ke struktur *Law & Economics* yang baru.\n\nSilakan gunakan **sidebar di kiri** untuk mengakses halaman analisis per hipotesis (H1–H5).")
st.stop()

# ── Styles ──
st.markdown("""
<style>
.metric-card {
    background: #1E1E1E;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}
.metric-value { font-size: 2.2rem; font-weight: 700; color: #4CAF50; margin-bottom: 5px; }
.metric-label { font-size: 0.95rem; color: #E0E0E0; margin-bottom: 5px; }
.metric-delta { font-size: 0.85rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
C_ASING = "#42A5F5"
C_DOMESTIK = "#66BB6A"
C_WARN = "#FF9800"
C_ANOMALY = "#E53935"

# ── Data Loading ──
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "final")

@st.cache_data
def load_data():
    df_a = pd.read_csv(os.path.join(DATA_DIR, "realisasi_investasi_asing.csv"), parse_dates=["date"])
    df_d = pd.read_csv(os.path.join(DATA_DIR, "realisasi_investasi_domestik.csv"), parse_dates=["date"])
    df_i = pd.read_csv(os.path.join(DATA_DIR, "icor_nasional.csv"), parse_dates=["date"])
    return df_a, df_d, df_i

@st.cache_data
def load_summary():
    stats = {}
    path = os.path.join(DATA_DIR, "icor_nasional.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            stats['icor_pma'] = df.iloc[-1].get('icor_pma', 0)
            stats['icor_year'] = str(df.iloc[-1].get('date', ''))[:4]
    path = os.path.join(DATA_DIR, "pmi_manufaktur.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            stats['pmi_latest'] = df.iloc[-1].get('pmi_index', 0)
    path = os.path.join(DATA_DIR, "capital_outflow.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            stats['outflow_latest'] = df.iloc[-1].get('net_sell_idr_tn', 0)
    path = os.path.join(DATA_DIR, "ikk_expect_vs_present.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            stats['ikk_gap'] = df.iloc[-1].get('ikk_gap', 0)
    return stats

@st.cache_data
def load_legal_summary():
    legal = {}
    # MA yearly
    p = os.path.join(DATA_DIR, "putusan_ma_yearly.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        legal['total_ma'] = int(df['total_putusan'].sum()) if not df.empty else 0
    # MK yearly
    p = os.path.join(DATA_DIR, "putusan_mk_yearly.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        legal['total_mk'] = int(df['total_putusan_mk'].sum()) if not df.empty else 0
    # SIPP yearly
    p = os.path.join(DATA_DIR, "sipp_yearly.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        legal['total_sipp'] = int(df['total_perkara'].sum()) if not df.empty else 0
    # Regulasi summary
    p = os.path.join(DATA_DIR, "regulasi_summary_per_hipotesis.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        legal['total_regulasi'] = int(df['count'].sum()) if not df.empty else 0
    # Churn rate
    p = os.path.join(DATA_DIR, "regulatory_churn_rate.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        if not df.empty:
            legal['churn_latest'] = df.iloc[-1].get('churn_rate', 0)
            legal['churn_year'] = int(df.iloc[-1].get('year', 0))
    # MA Statistik
    p = os.path.join(DATA_DIR, "laporan_ma_statistik.csv")
    if os.path.exists(p):
        df = pd.read_csv(p)
        if not df.empty:
            legal['reversal_rate'] = df.iloc[0].get('reversal_rate_pct', 0)
    return legal

# Initialize
df_asing, df_domestik, df_icor = load_data()
stats = load_summary()

# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.markdown('<div class="org-badge" style="background:#1B5E20; color:#E8F5E9; padding:4px 10px; border-radius:4px; font-size:0.8rem; font-weight:700; display:inline-block; margin-bottom:10px;">CELIOS — CENTER OF ECONOMIC AND LAW STUDIES</div>', unsafe_allow_html=True)
st.markdown('<h1 style="color:#66BB6A; margin-bottom:0px; padding-bottom:0px;">Legal Enforcement Uncertainty Index</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 1.1rem; color: #9E9E9E; margin-top: 5px;">Dashboard Analisis Risk Pricing Investasi Indonesia (H1–H5)<br>Riset 5 Narasi Strategis: Inconsistency, Selective Enforcement, Procedural, Regulatory Reversal, & Criminalization Risk.</p>', unsafe_allow_html=True)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# LAYER 1: VARIABEL HUKUM (KPI CARDS)
# ══════════════════════════════════════════════════
legal = load_legal_summary()

st.markdown("## Data Primer Penegakan Hukum")
st.markdown('<p style="font-size: 1.05rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">Overview Sumber Ketidakpastian Lingkungan Bisnis</p>', unsafe_allow_html=True)

with st.expander("Metodologi: Model Hukum → Ekonomi", expanded=False):
    st.markdown("""
    **Model Kausalitas:** `Penegakan Hukum (X) → Respons Ekonomi (Y)`
    
    Dashboard ini menggunakan model kausalitas untuk menyelaraskan narasi:
    - **Variabel Independen (X):** Data hukum primer — putusan pengadilan, regulasi, durasi sengketa
    - **Variabel Dependen (Y):** Data ekonomi — ICOR, IKK, PMI, Capital Outflow, Realisasi Investasi
    
    Pertanyaan riset: *"Apakah variabel hukum (X) mempengaruhi respons ekonomi (Y)?"*
    """)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --- Legal KPI Cards ---
lc1, lc2, lc3, lc4 = st.columns(4)
with lc1:
    total_kasus = legal.get('total_ma', 0) + legal.get('total_mk', 0) + legal.get('total_sipp', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Kasus Hukum Bisnis</div>
        <div class="metric-value" style="color:#AB47BC">{total_kasus}</div>
        <div class="metric-delta" style="color:#AB47BC">MA ({legal.get('total_ma',0)}) + MK ({legal.get('total_mk',0)}) + SIPP ({legal.get('total_sipp',0)})</div>
    </div>
    """, unsafe_allow_html=True)
with lc2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Regulasi Bisnis Aktif</div>
        <div class="metric-value" style="color:#42A5F5">{legal.get('total_regulasi', 0)}</div>
        <div class="metric-delta" style="color:#42A5F5">Tersebar di 5 hipotesis H1–H5</div>
    </div>
    """, unsafe_allow_html=True)
with lc3:
    churn = legal.get('churn_latest', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Regulatory Churn Rate</div>
        <div class="metric-value" style="color:#FF9800">{churn:.1f}%</div>
        <div class="metric-delta" style="color:#FF9800">Regulasi dicabut/diubah per tahun</div>
    </div>
    """, unsafe_allow_html=True)
with lc4:
    rev = legal.get('reversal_rate', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Reversal Rate MA</div>
        <div class="metric-value" style="color:#E53935">{rev:.2f}%</div>
        <div class="metric-delta" style="color:#E53935">Putusan MA yang dikabulkan (2023)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# LAYER 2: DAMPAK EKONOMI (KPI CARDS)
# ══════════════════════════════════════════════════
st.markdown("## Dampak Makroekonomi Nasional")
st.markdown('<p style="font-size: 1.05rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">Respons Pasar & Investor terhadap Ketidakpastian Hukum</p>', unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --- Economic KPI Cards ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    icor_val = stats.get('icor_pma', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ICOR Investasi Asing</div>
        <div class="metric-value" style="color:#EF5350">{icor_val:.2f}</div>
        <div class="metric-delta" style="color:#EF5350">▼ Cost of Capital Tembus &gt; 6.0</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    pmi = stats.get('pmi_latest', 0)
    pmi_col = "#66BB6A" if pmi >= 50 else "#EF5350"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">PMI Manufaktur</div>
        <div class="metric-value" style="color:{pmi_col}">{pmi:.1f}</div>
        <div class="metric-delta" style="color:{pmi_col}">Sinyal Kontraksi</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    outflow = stats.get('outflow_latest', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Capital Outflow (Net Sell)</div>
        <div class="metric-value" style="color:#EF5350">{outflow:.2f} T</div>
        <div class="metric-delta" style="color:#EF5350">Data Baseline 2024–2025</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    gap = stats.get('ikk_gap', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gap IKK (Exp vs Present)</div>
        <div class="metric-value" style="color:#FF9800">{gap:.1f}</div>
        <div class="metric-delta" style="color:#FF9800">Optimisme Semu Konsumen</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# BAGIAN H1 (GRAFIK OVERVIEW)
# ══════════════════════════════════════════════════
st.markdown("## 📈 Analisis H1: Dampak Inkonsistensi Hukum pada Distribusi Investasi")
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --- Helper logic for H1 ---
def gini_coefficient(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    arr = arr[arr >= 0]
    if len(arr) < 2 or arr.sum() == 0: return np.nan
    arr = np.sort(arr)
    n = len(arr)
    idx = np.arange(1, n + 1)
    return (2 * np.sum(idx * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr))

def calc_gini_q(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    g = prov_q.groupby("date")["nilai_idr_bn"].apply(gini_coefficient).reset_index()
    g.columns = ["date", "gini"]
    g["tipe"] = label
    return g

def calc_std_q(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    s = prov_q.groupby("date")["nilai_idr_bn"].std().reset_index()
    s.columns = ["date", "std_dev"]
    s["tipe"] = label
    return s

# ── 1.1 GINI COEFFICIENT ──
st.markdown("### 1.1 Ketimpangan Distribusi Investasi Antar Provinsi (Gini Coefficient)")
st.markdown("📁 **Sumber:** Agregasi per provinsi per kuartal dari `realisasi_investasi_asing.csv` & `realisasi_investasi_domestik.csv`.")
st.markdown("📊 **Visualisasi:** Line chart membandingkan Gini Coefficient PMA (biru) vs PMDN (hijau). Nilai > 0.4 menunjukkan ketimpangan di luar batas moderat.")

gini_a = calc_gini_q(df_asing, "Investasi Asing (PMA)")
gini_d = calc_gini_q(df_domestik, "Investasi Domestik (PMDN)")
gini_combined = pd.concat([gini_a, gini_d], ignore_index=True)

fig_gini = px.line(
    gini_combined, x="date", y="gini", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": C_ASING, "Investasi Domestik (PMDN)": C_DOMESTIK},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "gini": "Gini Coefficient", "tipe": "Tipe Investasi"}
)
fig_gini.update_layout(height=450, yaxis=dict(range=[0, 1]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified")
fig_gini.add_hline(y=0.4, line_dash="dash", line_color=C_WARN, annotation_text="Batas Ketimpangan Moderat (0.4)")
st.plotly_chart(fig_gini, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 1.2 STD DEVIATION ──
st.markdown("### 1.2 Volatilitas & Lebar Kesenjangan Investasi (Std. Deviation)")
st.markdown("📁 **Sumber:** Perhitungan standar deviasi dari distribusi investasi provinsi per kuartal.")
st.markdown("📊 **Visualisasi:** Line chart volatilitas sebaran investasi absolut. Spike menunjukkan kuartal dengan konsentrasi asimetris tinggi.")

std_a = calc_std_q(df_asing, "Investasi Asing (PMA)")
std_d = calc_std_q(df_domestik, "Investasi Domestik (PMDN)")
std_combined = pd.concat([std_a, std_d], ignore_index=True)

fig_std = px.line(
    std_combined, x="date", y="std_dev", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": C_ASING, "Investasi Domestik (PMDN)": C_DOMESTIK},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "std_dev": "Std. Deviation (IDR Bn)", "tipe": "Tipe Investasi"}
)
fig_std.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified")
st.plotly_chart(fig_std, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 1.3 TOP/BOTTOM PROVINSI ──
st.markdown("### 1.3 Peta Konsentrasi Investasi (Top vs Bottom Provinsi)")
st.markdown("📁 **Sumber:** Rata-rata investasi gabungan PMA+PMDN per provinsi dari keseluruhan periode data.")
st.markdown("📊 **Visualisasi:** Bar chart horizontal Top 15 (hijau) vs Bottom 15 (merah) menunjukkan dominasi absolut segelintir wilayah tujuan investasi.")

df_all = pd.concat([df_asing.assign(tipe="Asing"), df_domestik.assign(tipe="Domestik")], ignore_index=True)
prov_avg = df_all.groupby("provinsi")["nilai_idr_bn"].mean().sort_values(ascending=True).reset_index()
prov_avg.columns = ["provinsi", "rata_rata"]

tab_top, tab_bottom = st.tabs(["Top 15 Provinsi", "Bottom 15 Provinsi"])
with tab_top:
    top = prov_avg.tail(15)
    fig_top = px.bar(
        top, x="rata_rata", y="provinsi", orientation="h", color="rata_rata",
        color_continuous_scale=["#1B5E20", "#43A047", "#A5D6A7"], template=PLOTLY_TEMPLATE,
        labels={"rata_rata": "Rata-rata (IDR Bn / Miliar/kuartal)", "provinsi": ""}
    )
    fig_top.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_top, use_container_width=True)

with tab_bottom:
    bottom = prov_avg.head(15)
    fig_bot = px.bar(
        bottom, x="rata_rata", y="provinsi", orientation="h", color="rata_rata",
        color_continuous_scale=["#B71C1C", "#E53935", "#EF9A9A"], template=PLOTLY_TEMPLATE,
        labels={"rata_rata": "Rata-rata (IDR Bn / Miliar/kuartal)", "provinsi": ""}
    )
    fig_bot.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_bot, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 1.4 ICOR ──
st.markdown("### 1.4 Tren ICOR Nasional: Biaya Ketidakpastian")
st.markdown("📁 **Sumber:** `icor_nasional.csv` - Rasio Pembentukan Modal Tetap Bruto terhadap Pertumbuhan PDB.")
st.markdown("📊 **Visualisasi:** Line chart perbandingan efisiensi investasi PMDN (hijau) dan PMA (biru). Spike menandakan fase inefisiensi prosedural yang parah.")

fig_icor = go.Figure()
fig_icor.add_trace(go.Scatter(x=df_icor["date"], y=df_icor["icor_pmdn"], mode="lines+markers", name="ICOR PMDN", line=dict(color=C_DOMESTIK, width=2.5), marker=dict(size=7)))
fig_icor.add_trace(go.Scatter(x=df_icor["date"], y=df_icor["icor_pma"], mode="lines+markers", name="ICOR PMA", line=dict(color=C_ASING, width=2.5), marker=dict(size=7)))
fig_icor.update_layout(template=PLOTLY_TEMPLATE, height=400, yaxis_title="ICOR (Rasio)", xaxis_title="Tahun", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=10, b=20), hovermode="x unified")
st.plotly_chart(fig_icor, use_container_width=True)

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div class="footer">
    CELIOS — Center of Economic and Law Studies | Legal Enforcement Uncertainty Index (LEUI) | 2026
</div>
""", unsafe_allow_html=True)
