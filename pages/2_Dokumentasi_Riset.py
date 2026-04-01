import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

st.set_page_config(
    page_title="Dokumentasi Riset — CELIOS LEUI",
    page_icon="📑",
    layout="wide"
)
render_sidebar()

# --- Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

.page-header {
    font-size: 2rem;
    font-weight: 700;
    color: #E0E0E0;
    margin-bottom: 0.3rem;
}
.page-sub {
    font-size: 0.95rem;
    color: #757575;
    margin-bottom: 2rem;
}

.doc-meta {
    display: flex;
    gap: 16px;
    margin-bottom: 1rem;
}
.meta-chip {
    background: #1565C022;
    color: #42A5F5;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
}

.doc-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}
.doc-content th {
    background: #232B3B;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 0.85rem;
    border-bottom: 2px solid #1565C0;
}
.doc-content td {
    padding: 8px 14px;
    border-bottom: 1px solid #ffffff0a;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(_('<div class="page-header">Dokumentasi Riset</div>'), unsafe_allow_html=True)
st.markdown(_('<div class="page-sub">Preview dan download dokumen riset LEUI — pilih dokumen dari sidebar untuk membaca</div>'), unsafe_allow_html=True)

# --- Docs directory ---
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

# --- Available documents ---
docs_map = {
    _("📐 Framework LEUI"): {
        "file": "framework_LEUI.md",
        "desc": _("Premis dasar, causal chain, 5 hipotesis (H1-H5), mekanisme risk pricing"),
        "tags": [_("Framework"), _("5 Hipotesis"), _("Causal Chain")]
    },
    _("📑 Strategi Narasi & Arah Analisis"): {
        "file": "strategi_narasi_LEUI.md",
        "desc": _("100% dari brief: premis, hipotesis, indikator, narasi per H1-H5, metode olah data"),
        "tags": [_("Strategy"), _("Brief-based"), _("5 Narasi")]
    },
    _("📊 Laporan Insight Data"): {
        "file": "report_insight_data_LEUI.md",
        "desc": _("Audit 5 file Excel, mapping data ke framework, identifikasi data gap"),
        "tags": [_("Data Report"), _("5 Datasets"), _("Gap Analysis")]
    },
    _("🔬 Metodologi Teknis"): {
        "file": "metodologi_teknis_report.md",
        "desc": _("Pipeline data: parsing, cleaning, konstruksi indikator, analisis statistik, dashboard"),
        "tags": [_("Technical"), _("Pipeline"), _("6 Steps")]
    },
}

# --- Sidebar doc selector ---
with st.sidebar:
    st.markdown(_("### 📂 Pilih Dokumen"))
    selected_doc = st.radio(
        _("Dokumen:"),
        list(docs_map.keys()),
        label_visibility="collapsed"
    )

# --- Load and render ---
doc_info = docs_map[selected_doc]
doc_path = os.path.join(DOCS_DIR, doc_info["file"])

# Meta tags
tags_html = " ".join([f'<span class="meta-chip">{tag}</span>' for tag in doc_info["tags"]])
st.markdown(f'<div class="doc-meta">{tags_html}</div>', unsafe_allow_html=True)
st.markdown(f"*{doc_info['desc']}*")
st.markdown("---")

# Render markdown
if os.path.exists(doc_path):
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    st.markdown(content, unsafe_allow_html=True)

    # Download
    st.markdown("---")
    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        st.download_button(
            label=f"⬇️ " + _("Download") + f" {doc_info['file']}",
            data=content,
            file_name=doc_info["file"],
            mime="text/markdown",
            use_container_width=True,
        )
else:
    st.error(_("File tidak ditemukan:") + f" `{doc_path}`")
    st.info(_("Pastikan file .md sudah ada di folder `docs/`"))
