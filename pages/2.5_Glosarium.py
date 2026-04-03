"""
Glosarium — Daftar istilah teknis dan konsep yang digunakan dalam riset LEUI.
"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

st.set_page_config(
    page_title="Glosarium — CELIOS LEUI",
    page_icon="ref/Celios China-Indonesia Energy Transition.png",
    layout="wide"
)
render_sidebar()

st.title(_("Glosarium & Daftar Istilah"))
subtitle = _("Referensi istilah teknis, indikator, dan konsep yang digunakan dalam riset LEUI")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

st.markdown("""
<div style="background:#1E1E1E; padding:15px; border-radius:10px; border-left: 5px solid #2196F3; margin-bottom: 20px;">
    Dokumen ini disusun untuk publik umum, pengambil kebijakan, dan peneliti agar dapat memahami
    istilah-istilah yang digunakan dalam dashboard dan laporan riset LEUI tanpa latar belakang
    teknis khusus.
</div>
""", unsafe_allow_html=True)

# ── Search ──
search = st.text_input(_("🔍 Cari istilah..."), "")

# ── Glossary Data ──
glossary = [
    # === Konsep Inti LEUI ===
    {"Istilah": "LEUI", "Kategori": "Konsep Inti",
     "Definisi": "Legal Enforcement Uncertainty Index — Indeks yang mengukur dampak ketidakpastian penegakan hukum terhadap keputusan investasi.",
     "Konteks": "Kerangka utama riset ini"},
    {"Istilah": "Inconsistency Risk (H1)", "Kategori": "Hipotesis",
     "Definisi": "Risiko bahwa penegakan hukum tidak konsisten antar wilayah, sektor, dan waktu — menghasilkan outcome uncertainty bagi investor.",
     "Konteks": "Kasus serupa mendapat putusan berbeda di daerah berbeda"},
    {"Istilah": "Selective Enforcement (H2)", "Kategori": "Hipotesis",
     "Definisi": "Risiko bahwa penegakan hukum bersifat selektif dan transaksional, hanya muncul saat ada momentum politik tertentu.",
     "Konteks": "Hukum dipakai sebagai alat negosiasi, bukan perlindungan"},
    {"Istilah": "Procedural Uncertainty (H3)", "Kategori": "Hipotesis",
     "Definisi": "Risiko dari proses hukum yang panjang, tidak pasti, dan mahal — menciptakan delay cost bagi investasi.",
     "Konteks": "Kasus pidana berjalan paralel dengan PTUN/perdata"},
    {"Istilah": "Regulatory Reversal (H4)", "Kategori": "Hipotesis",
     "Definisi": "Risiko bahwa regulasi atau izin yang sudah sah tiba-tiba dicabut atau diubah, menciptakan stranded asset.",
     "Konteks": "Perizinan sah → tiba-tiba melanggar aturan baru"},
    {"Istilah": "Criminalization Risk (H5)", "Kategori": "Hipotesis",
     "Definisi": "Risiko bahwa keputusan bisnis atau kebijakan administratif dikriminalisasi, meningkatkan risiko personal bagi investor dan manajemen.",
     "Konteks": "Direksi dijerat pidana atas keputusan bisnis"},
    {"Istilah": "Causal Chain", "Kategori": "Konsep Inti",
     "Definisi": "Rantai sebab-akibat riset: Penegakan Hukum → Ketidakpastian → Persepsi Risiko → Risk Pricing → Keputusan Investasi.",
     "Konteks": "Kerangka logika utama LEUI"},
    {"Istilah": "Risk Pricing", "Kategori": "Konsep Inti",
     "Definisi": "Proses di mana investor mengkonversi ketidakpastian hukum menjadi biaya ekonomi yang terukur (premium, delay, insurance).",
     "Konteks": "Investor tidak bilang 'hukum buruk', tapi minta higher return"},
    {"Istilah": "Proxy Data", "Kategori": "Konsep Inti",
     "Definisi": "Data pengganti yang digunakan sebagai pendekatan ketika data ideal (putusan pengadilan, kasus hukum) belum tersedia.",
     "Konteks": "Realisasi investasi digunakan sebagai proxy inkonsistensi hukum"},

    # === Indikator Statistik ===
    {"Istilah": "Gini Coefficient", "Kategori": "Indikator Statistik",
     "Definisi": "Ukuran ketimpangan distribusi. Nilai 0 = merata sempurna, 1 = sangat timpang. Dalam konteks LEUI, digunakan untuk mengukur konsentrasi investasi antar provinsi.",
     "Konteks": "Gini > 0.4 dianggap ketimpangan moderat-tinggi"},
    {"Istilah": "Standard Deviation (SD)", "Kategori": "Indikator Statistik",
     "Definisi": "Ukuran sebaran/volatilitas data dari rata-ratanya. SD tinggi = data sangat bervariasi. Dalam LEUI, mengukur seberapa jauh investasi antar provinsi berbeda satu sama lain.",
     "Konteks": "SD investasi antar provinsi per kuartal"},
    {"Istilah": "ICOR", "Kategori": "Indikator Ekonomi",
     "Definisi": "Incremental Capital-Output Ratio — rasio yang mengukur berapa unit investasi dibutuhkan untuk menghasilkan 1 unit pertumbuhan PDB. ICOR tinggi = investasi tidak efisien.",
     "Konteks": "ICOR naik → biaya investasi makin mahal, salah satunya akibat ketidakpastian hukum"},
    {"Istilah": "IKK", "Kategori": "Indikator Ekonomi",
     "Definisi": "Indeks Kepercayaan Konsumen — survei Bank Indonesia yang mengukur optimisme/pesimisme konsumen terhadap kondisi ekonomi. Terbagi menjadi IKK Ekspektasi (masa depan) dan IKK Present (saat ini).",
     "Konteks": "Gap antara Ekspektasi dan Present = sinyal ketidakpastian"},
    {"Istilah": "PMI", "Kategori": "Indikator Ekonomi",
     "Definisi": "Purchasing Managers' Index — indeks aktivitas manufaktur. PMI > 50 = ekspansi, PMI < 50 = kontraksi. Sumber: S&P Global.",
     "Konteks": "Leading indicator aktivitas ekonomi riil"},
    {"Istilah": "Capital Outflow / Net Sell", "Kategori": "Indikator Ekonomi",
     "Definisi": "Arus keluar modal asing, diukur dari net sell (penjualan bersih) obligasi oleh investor asing. Spike net sell = investor asing melarikan modal.",
     "Konteks": "Proxy untuk regulatory reversal risk (H4)"},
    {"Istilah": "Event Study", "Kategori": "Metode Analisis",
     "Definisi": "Metode yang meng-overlay timeline peristiwa tertentu (krisis politik, pencabutan izin) terhadap pergerakan indikator ekonomi untuk melihat dampak kausal.",
     "Konteks": "Digunakan di H2 untuk Selective Enforcement"},
    {"Istilah": "Anomaly Detection (Z-Score)", "Kategori": "Metode Analisis",
     "Definisi": "Metode untuk mendeteksi nilai yang secara statistik tidak biasa (outlier). Z-Score > 2 atau < -2 dianggap anomali.",
     "Konteks": "Digunakan di H4 untuk mendeteksi spike capital outflow"},
    {"Istilah": "Gap Analysis", "Kategori": "Metode Analisis",
     "Definisi": "Analisis selisih antara dua indikator yang seharusnya bergerak searah. Pelebaran gap = sinyal divergensi.",
     "Konteks": "Digunakan di H5 untuk IKK Ekspektasi vs Present"},

    # === Data & Sumber ===
    {"Istilah": "PMA", "Kategori": "Investasi",
     "Definisi": "Penanaman Modal Asing — investasi yang berasal dari entitas asing ke Indonesia. Dikoordinasikan oleh BKPM.",
     "Konteks": "Data per provinsi/kabupaten dari CEIC/BKPM"},
    {"Istilah": "PMDN", "Kategori": "Investasi",
     "Definisi": "Penanaman Modal Dalam Negeri — investasi yang berasal dari entitas domestik Indonesia.",
     "Konteks": "Data per provinsi/kabupaten dari CEIC/BKPM"},
    {"Istilah": "Realisasi Investasi", "Kategori": "Investasi",
     "Definisi": "Nilai investasi yang benar-benar terealisasi (bukan rencana/izin), dilaporkan per kuartal per kabupaten/kota.",
     "Konteks": "394 kabupaten/kota, data kuartalan 1990–2025"},
    {"Istilah": "CEIC", "Kategori": "Sumber Data",
     "Definisi": "Platform data ekonomi dan statistik global (CDMNext). Sumber utama data mentah dalam riset ini.",
     "Konteks": "File Excel mentah berasal dari CEIC database"},
    {"Istilah": "BKPM", "Kategori": "Sumber Data",
     "Definisi": "Badan Koordinasi Penanaman Modal — lembaga pemerintah yang mengelola data realisasi investasi PMA dan PMDN.",
     "Konteks": "Sumber asli data investasi"},
    {"Istilah": "BPS", "Kategori": "Sumber Data",
     "Definisi": "Badan Pusat Statistik — lembaga pemerintah yang menerbitkan data PDB, ICOR, dan statistik ekonomi lainnya.",
     "Konteks": "Sumber data ICOR nasional"},

    # === Istilah Teknis Tambahan ===
    {"Istilah": "Risk Premium", "Kategori": "Ekonomi",
     "Definisi": "Tambahan imbal hasil yang diminta investor sebagai kompensasi atas risiko tambahan. Semakin tinggi ketidakpastian, semakin besar risk premium.",
     "Konteks": "Legal uncertainty → risk premium naik → cost of capital naik"},
    {"Istilah": "Cost of Capital", "Kategori": "Ekonomi",
     "Definisi": "Biaya yang harus ditanggung perusahaan untuk mendapatkan modal (utang atau ekuitas). Ketidakpastian hukum menaikkan cost of capital.",
     "Konteks": "ICOR sebagai proxy cost of capital"},
    {"Istilah": "Stranded Asset", "Kategori": "Ekonomi",
     "Definisi": "Aset yang kehilangan nilai sebelum akhir masa manfaatnya, biasanya karena perubahan regulasi mendadak.",
     "Konteks": "Risiko dari regulatory reversal (H4)"},
    {"Istilah": "Delay Cost", "Kategori": "Ekonomi",
     "Definisi": "Biaya yang timbul dari keterlambatan — proses hukum berlarut-larut, izin yang tertahan, atau keputusan yang ditunda.",
     "Konteks": "Procedural uncertainty (H3) menciptakan delay cost"},
    {"Istilah": "Outcome Uncertainty", "Kategori": "Ekonomi",
     "Definisi": "Ketidakpastian terhadap hasil akhir — investor tidak bisa memprediksi bagaimana hukum akan diterapkan pada kasusnya.",
     "Konteks": "Tipe ketidakpastian dari Inconsistency Risk (H1)"},
    {"Istilah": "Dual Economy", "Kategori": "Ekonomi",
     "Definisi": "Kondisi di mana beberapa wilayah berkembang pesat sementara mayoritas tertinggal, menciptakan dua 'ekonomi' dalam satu negara.",
     "Konteks": "Dampak dari konsentrasi investasi di 'zona aman'"},
    {"Istilah": "CDS (Credit Default Swap)", "Kategori": "Ekonomi",
     "Definisi": "Instrumen keuangan yang mengukur risiko gagal bayar suatu negara. CDS Indonesia yang tinggi = persepsi risiko negara tinggi.",
     "Konteks": "Data ideal untuk country risk, belum tersedia dalam dataset ini"},
]

df_glos = pd.DataFrame(glossary)

# Filter by search
if search:
    mask = (
        df_glos['Istilah'].str.contains(search, case=False, na=False) |
        df_glos['Definisi'].str.contains(search, case=False, na=False) |
        df_glos['Kategori'].str.contains(search, case=False, na=False)
    )
    df_glos = df_glos[mask]

# Category filter
categories = sorted(df_glos['Kategori'].unique())
selected_cat = st.multiselect(_("Filter Kategori:"), categories, default=categories)
df_glos = df_glos[df_glos['Kategori'].isin(selected_cat)]

st.markdown(f"**{len(df_glos)} istilah** ditemukan")
st.markdown("---")

# Display grouped by category
for cat in sorted(df_glos['Kategori'].unique()):
    st.markdown(f"### {cat}")
    cat_items = df_glos[df_glos['Kategori'] == cat].sort_values('Istilah')

    for _, row in cat_items.iterrows():
        st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 18px; border-radius:8px; margin-bottom:8px; border-left:3px solid #43A047;">
    <strong style="color:#66BB6A; font-size:1.05rem;">{row['Istilah']}</strong><br>
    <span style="color:#E0E0E0;">{row['Definisi']}</span><br>
    <small style="color:#9E9E9E;">💡 {row['Konteks']}</small>
</div>
""", unsafe_allow_html=True)

    st.markdown("")

# Footer
st.markdown("---")
st.caption(_("Glosarium ini disusun berdasarkan kerangka riset LEUI dan akan terus diperbarui seiring perkembangan analisis."))
