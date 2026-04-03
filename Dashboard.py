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

# --- Load summary data ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")

@st.cache_data
def load_summary():
    stats = {}
    # ICOR
    path = os.path.join(DATA_DIR, "icor_nasional.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            latest = df.iloc[-1]
            stats['icor_pmdn'] = latest.get('icor_pmdn', 0)
            stats['icor_pma'] = latest.get('icor_pma', 0)
            stats['icor_year'] = str(latest.get('date', ''))[:4]
    # PMI
    path = os.path.join(DATA_DIR, "pmi_manufaktur.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            stats['pmi_latest'] = df.iloc[-1].get('pmi_index', 0)
            stats['pmi_date'] = str(df.iloc[-1].get('date', ''))[:7]
    # Capital Outflow
    path = os.path.join(DATA_DIR, "capital_outflow.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            stats['outflow_latest'] = df.iloc[-1].get('net_sell_idr_tn', 0)
            stats['outflow_mean'] = df['net_sell_idr_tn'].mean()
            stats['outflow_max'] = df['net_sell_idr_tn'].max()
    # IKK
    path = os.path.join(DATA_DIR, "ikk_expect_vs_present.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            latest = df.iloc[-1]
            stats['ikk_expect'] = latest.get('ikk_expectation', 0)
            stats['ikk_present'] = latest.get('ikk_present', 0)
            stats['ikk_gap'] = latest.get('ikk_gap', 0)
            stats['ikk_date'] = str(latest.get('date', ''))[:7]
            stats['ikk_rows'] = len(df)
    # Investment
    path = os.path.join(DATA_DIR, "realisasi_investasi_domestik.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        stats['invest_domestik_rows'] = len(df)
        stats['invest_domestik_prov'] = df['provinsi'].nunique() if 'provinsi' in df.columns else 0
    path = os.path.join(DATA_DIR, "realisasi_investasi_asing.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        stats['invest_asing_rows'] = len(df)
    return stats

stats = load_summary()

# --- KPI Cards ---
st.markdown("### Snapshot Indikator Terkini")

col1, col2, col3, col4 = st.columns(4)

with col1:
    icor_val = stats.get('icor_pma', 0)
    icor_year = stats.get('icor_year', '—')
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">ICOR PMA</div>
        <div class="stat-number">{icor_val:.2f}</div>
        <div class="stat-sub">Cost of Capital ({icor_year})</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    pmi = stats.get('pmi_latest', 0)
    pmi_color = "#66BB6A" if pmi >= 50 else "#EF5350"
    pmi_status = "Ekspansi" if pmi >= 50 else "Kontraksi"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">PMI Manufaktur</div>
        <div class="stat-number" style="color: {pmi_color}">{pmi:.1f}</div>
        <div class="stat-sub">{pmi_status} ({stats.get('pmi_date', '—')})</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    outflow = stats.get('outflow_latest', 0)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Capital Outflow (Net Sell)</div>
        <div class="stat-number" style="color: #EF5350">{outflow:.2f} T</div>
        <div class="stat-sub">IDR Triliun (terbaru)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    gap = stats.get('ikk_gap', 0)
    gap_color = "#66BB6A" if gap > 0 else "#EF5350"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">IKK Gap (Expectation − Present)</div>
        <div class="stat-number" style="color: {gap_color}">{gap:.1f}</div>
        <div class="stat-sub">Consumer Confidence ({stats.get('ikk_date', '—')})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# --- Framework Summary ---
st.markdown("---")
st.markdown("### Kerangka Riset LEUI")

st.markdown("""
> **Premis:** Bukan hukum buruk yang paling mahal, tapi **hukum yang tak bisa diprediksi.**

**Causal Chain:** Penegakan Hukum → Ketidakpastian → Persepsi Risiko → Risk Pricing → Keputusan Investasi
""")

col_h1, col_h2 = st.columns(2)

with col_h1:
    st.markdown("""
    **5 Hipotesis:**
    | # | Hipotesis | Uncertainty Type |
    |---|-----------|-----------------|
    | H1 | Inconsistency Risk | Outcome uncertainty |
    | H2 | Selective Enforcement | Political risk |
    | H3 | Procedural Uncertainty | Process risk |
    | H4 | Regulatory Reversal | Policy risk |
    | H5 | Criminalization Risk | Personal risk |
    """)

with col_h2:
    st.markdown("""
    **Risk Pricing Channels:**
    | Jenis Risiko | Cara Di-price |
    |---|---|
    | Legal uncertainty | Risk premium ↑ |
    | Enforcement risk | Cost of capital ↑ |
    | Criminalization risk | Insurance cost ↑ |
    | Process risk | Delay cost ↑ |
    | Regulatory reversal | Expected return ↓ |
    """)

# --- Data inventory ---
st.markdown("---")
st.markdown("### Inventaris Data")

inv_data = [
    {"Dataset": "Biaya Investasi (ICOR)", "Rows": "15", "Period": "2010-2024", "Freq": "Yearly"},
    {"Dataset": "Realisasi Investasi Domestik", "Rows": str(stats.get('invest_domestik_rows', '-')), "Period": "1990-2025", "Freq": "Quarterly"},
    {"Dataset": "Realisasi Investasi Asing", "Rows": str(stats.get('invest_asing_rows', '-')), "Period": "1990-2025", "Freq": "Quarterly"},
    {"Dataset": "IKK (Expect vs Present)", "Rows": str(stats.get('ikk_rows', '-')), "Period": "2001-2025", "Freq": "Monthly"},
    {"Dataset": "PMI Manufaktur", "Rows": "36", "Period": "2023-2026", "Freq": "Monthly"},
    {"Dataset": "Capital Outflow", "Rows": "32", "Period": "Dec 2024-Jan 2026", "Freq": "Daily"},
]
st.dataframe(pd.DataFrame(inv_data), use_container_width=True, hide_index=True)

# --- Navigation Cards ---
st.markdown("---")
st.markdown("### Navigasi")

col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-title">Eksplorasi Data</div>
        <div class="nav-desc">Akses langsung ke semua dataset CSV — filter, preview, dan download</div>
    </div>
    """, unsafe_allow_html=True)

with col_nav2:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-title">Dokumentasi Riset</div>
        <div class="nav-desc">Framework LEUI, strategi narasi, metodologi teknis, dan insight data</div>
    </div>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div class="footer">
    CELIOS — Center of Economic and Law Studies | Legal Enforcement Uncertainty Index (LEUI) | 2026
</div>
""", unsafe_allow_html=True)
