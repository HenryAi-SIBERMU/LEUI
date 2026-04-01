import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.data_loader import get_all_csvs, load_csv
from src.utils.i18n import _

st.set_page_config(
    page_title="Eksplorasi Data — CELIOS LEUI",
    page_icon="ref/Celios China-Indonesia Energy Transition.png",
    layout="wide"
)

render_sidebar()

# --- Main Content ---
st.title(_("Eksplorasi Data (Repository)"))
st.markdown(_("""
<div style="background-color:#1E1E1E; padding:15px; border-radius:10px; border-left: 5px solid #2196F3; margin-bottom: 20px;">
    <strong>Pusat Data & Download:</strong><br>
    Halaman ini menyediakan akses langsung ke semua <b>dataset CSV</b> yang telah di-parse dari file Excel mentah di <code>ref/datamentah/</code>.
</div>
"""), unsafe_allow_html=True)

# --- Get all CSVs ---
csv_files = get_all_csvs()

if not csv_files:
    st.error(_("Tidak ada file CSV ditemukan di data/processed/. Jalankan parse_ref.py terlebih dahulu."))
    st.stop()

# --- Dataset selector ---
selected_file = st.selectbox(
    _("Pilih Dataset:"),
    list(csv_files.keys()),
    format_func=lambda x: x.replace('.csv', '').replace('_', ' ').title()
)

# --- Load and display ---
df = pd.read_csv(csv_files[selected_file])

# Info bar
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric(_("Rows"), f"{len(df):,}")
with col_info2:
    st.metric(_("Columns"), str(len(df.columns)))
with col_info3:
    size_kb = os.path.getsize(csv_files[selected_file]) / 1024
    st.metric(_("Size"), f"{size_kb:.0f} KB")

# Column info
with st.expander(_("Info Kolom"), expanded=False):
    col_info = pd.DataFrame({
        'Kolom': df.columns,
        'Tipe': [str(df[c].dtype) for c in df.columns],
        'Non-Null': [df[c].notna().sum() for c in df.columns],
        'Sample': [str(df[c].iloc[0]) if len(df) > 0 else '' for c in df.columns]
    })
    st.dataframe(col_info, use_container_width=True, hide_index=True)

# Statistics
with st.expander(_("Statistik Deskriptif"), expanded=False):
    st.dataframe(df.describe(), use_container_width=True)

# Data viewer
st.subheader(_("Data"))
st.dataframe(df, use_container_width=True)

# Download
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(
    _("Download CSV"),
    csv_data,
    selected_file,
    "text/csv",
    key='download-csv'
)
