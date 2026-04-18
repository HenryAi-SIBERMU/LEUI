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
    <strong>Pusat Data &amp; Download:</strong><br>
    Halaman ini menyediakan akses langsung ke semua <b>dataset CSV</b> yang telah di-parse dari file Excel mentah di <code>ref/datamentah/</code>.
</div>
"""), unsafe_allow_html=True)

# --- Get all CSVs ---
csv_files = get_all_csvs()

if not csv_files:
    st.error(_("Tidak ada file CSV ditemukan di direktori data/final/. Pastikan pipeline data telah dijalankan."))
    st.stop()

# --- Dataset selector ---
selected_file = st.selectbox(
    _("Pilih Dataset:"),
    list(csv_files.keys()),
    format_func=lambda x: x.replace('.csv', '').replace('_', ' ').title()
)

# --- Load data ---
df = pd.read_csv(csv_files[selected_file])

# --- Format toggle (Long vs Wide) ---
is_pivotable = 'kabupaten' in df.columns and 'nilai_idr_bn' in df.columns
if is_pivotable:
    view_mode = st.radio(
        _("Format Tampilan:"),
        ["Long (Default)", "Wide (Seperti Excel)"],
        horizontal=True
    )
    if view_mode == "Wide (Seperti Excel)":
        df['label'] = df['provinsi'] + ': ' + df['kabupaten']
        df_wide = df.pivot_table(index='date', columns='label', values='nilai_idr_bn', aggfunc='first')
        df_wide = df_wide.sort_index()
        df_display = df_wide
    else:
        df_display = df
else:
    df_display = df

# Info bar
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric(_("Rows"), f"{len(df_display):,}")
with col_info2:
    st.metric(_("Columns"), str(len(df_display.columns)))
with col_info3:
    size_kb = os.path.getsize(csv_files[selected_file]) / 1024
    st.metric(_("Size"), f"{size_kb:.0f} KB")

# Column info
with st.expander(_("Info Kolom"), expanded=False):
    col_info = pd.DataFrame({
        'Kolom': df_display.columns,
        'Tipe': [str(df_display[c].dtype) for c in df_display.columns],
        'Non-Null': [df_display[c].notna().sum() for c in df_display.columns],
        'Sample': [str(df_display[c].iloc[0]) if len(df_display) > 0 else '' for c in df_display.columns]
    })
    st.dataframe(col_info, use_container_width=True, hide_index=True)

# Statistics
with st.expander(_("Statistik Deskriptif"), expanded=False):
    st.dataframe(df_display.describe(), use_container_width=True)

# Data viewer
st.subheader(_("Data"))
st.dataframe(df_display, use_container_width=True)

# Download
csv_data = df_display.to_csv().encode('utf-8')
st.download_button(
    _("Download CSV"),
    csv_data,
    selected_file,
    "text/csv",
    key='download-csv'
)
