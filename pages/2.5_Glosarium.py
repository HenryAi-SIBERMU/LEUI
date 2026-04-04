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
    {"Istilah": "Sporadis", "Kategori": "Istilah Teknis",
     "Definisi": "Sesuatu yang terjadi secara tidak menentu, terpencar-pencar, dan jarang. Dalam konteks LEUI, merujuk pada shock (kejutan) ekonomi yang muncul mendadak tanpa pola reguler.",
     "Konteks": "Penurunan kepercayaan publik terjadi secara sporadis (tiba-tiba), bukan gradual memburuk."},
    {"Istilah": "Volatilitas / Volatile", "Kategori": "Istilah Teknis",
     "Definisi": "Ukuran seberapa cepat dan ekstrem suatu indikator berubah/berfluktuasi dari waktu ke waktu. Sangat volatile = sangat mudah berubah naik-turun secara drastis.",
     "Konteks": "Data gap IKK yang sangat volatile menandakan struktur perspesi risiko yang rapuh."},
    {"Istilah": "IDR Bn / Miliar", "Kategori": "Investasi",
     "Definisi": "Miliar Rupiah (Billion = Miliar). Digunakan untuk menstandarisasi pelaporan nilai finansial yang masif dengan cara menghilangkan sembilan angka nol di belakangnya.",
     "Konteks": "Satuan nilai untuk laporan realisasi investasi tingkat provinsi di LEUI."},

    # === Istilah H4: Regulatory Reversal ===
    {"Istilah": "Capital Flight", "Kategori": "Ekonomi",
     "Definisi": "Pelarian modal — investor menarik dana secara masif dan cepat dari suatu negara, biasanya dipicu oleh ketidakpastian regulasi, krisis politik, atau perubahan kebijakan mendadak.",
     "Konteks": "Net sell obligasi yang melonjak tajam mengindikasikan capital flight (H4)."},
    {"Istilah": "Rolling Band Analysis", "Kategori": "Metode Analisis",
     "Definisi": "Metode visualisasi yang menampilkan rata-rata bergerak (rolling mean) beserta batas atas dan bawah (biasanya mean ± 2 standar deviasi). Data yang menembus batas atas = episode abnormal.",
     "Konteks": "Digunakan di H4 untuk mengidentifikasi capital flight episode yang melampaui fluktuasi wajar."},
    {"Istilah": "Volatility Clustering", "Kategori": "Istilah Teknis",
     "Definisi": "Fenomena di mana periode volatilitas tinggi cenderung diikuti oleh volatilitas tinggi lagi, dan sebaliknya. Artinya, ketidakpastian datang dalam gelombang, bukan tersebar merata.",
     "Konteks": "Di H4, rolling band yang melebar di periode tertentu menunjukkan volatility clustering pada capital outflow."},
    {"Istilah": "Coefficient of Variation (CV)", "Kategori": "Indikator Statistik",
     "Definisi": "Rasio antara standar deviasi dan rata-rata, dinyatakan dalam persen. CV tinggi = data sangat bervariasi relatif terhadap rata-ratanya. Mengukur volatilitas relatif.",
     "Konteks": "CV net sell obligasi yang tinggi menunjukkan capital outflow sangat tidak stabil (H4)."},
    {"Istilah": "IDR Tn / Triliun", "Kategori": "Investasi",
     "Definisi": "Triliun Rupiah. Satuan yang digunakan untuk mencatat volume net sell obligasi dan arus modal keluar.",
     "Konteks": "Satuan nilai capital outflow di H4."},
    {"Istilah": "Quarterly Aggregation", "Kategori": "Metode Analisis",
     "Definisi": "Metode pengelompokan data per kuartal (3 bulan) untuk melihat tren makro yang lebih jelas, menghilangkan noise dari fluktuasi mingguan/harian.",
     "Konteks": "Digunakan di H4 untuk mengidentifikasi kuartal terburuk capital outflow."},

    # === Istilah H5: Criminalization Risk ===
    {"Istilah": "Expectation Collapse", "Kategori": "Ekonomi",
     "Definisi": "Runtuhnya ekspektasi publik secara mendadak — masyarakat tiba-tiba kehilangan optimisme terhadap kondisi ekonomi masa depan, terukur dari penurunan tajam IKK Ekspektasi.",
     "Konteks": "Proxy utama untuk criminalization shock di H5."},
    {"Istilah": "Expectation Crash", "Kategori": "Istilah Teknis",
     "Definisi": "Episode spesifik di mana IKK Ekspektasi jatuh secara abnormal dalam satu bulan (Z-Score < -2). Penurunan terlalu tajam untuk dijelaskan oleh siklus ekonomi biasa.",
     "Konteks": "Terdeteksi algoritmik di H5 sebagai sinyal criminalization shock."},
    {"Istilah": "Episode / Episode Krisis", "Kategori": "Metode Analisis",
     "Definisi": "Suatu rentang waktu spesifik atau titik kejadian yang terdeteksi secara statistik menyimpang dari kondisi normal (contoh: Z-Score melewati ambang batas). Digunakan untuk menandai anomali tanpa harus menebak penyebab tunggalnya secara subjektif.",
     "Konteks": "Digunakan di H4 dan H5 untuk mendeteksi 'capital flight episode' dan 'expectation crash episode' murni berdasarkan algoritma statistik."},
    {"Istilah": "Chilling Effect", "Kategori": "Hukum",
     "Definisi": "Efek pendinginan — ketika satu kasus kriminalisasi membuat pihak lain yang tidak terlibat turut takut bertindak, menghambat pengambilan keputusan secara keseluruhan.",
     "Konteks": "Kriminalisasi satu direksi membuat ribuan direksi lain takut tanda tangan keputusan bisnis (H5)."},
    {"Istilah": "Personal Liability Risk", "Kategori": "Hukum",
     "Definisi": "Risiko bahwa individu (direksi, pejabat, manajer) secara pribadi dijerat hukum atas keputusan bisnis atau kebijakan yang diambilnya dalam kapasitas resmi.",
     "Konteks": "Komponen utama criminalization risk di H5 — direksi dijerat pidana, pejabat takut tanda tangan."},
    {"Istilah": "Spearman Rank Correlation", "Kategori": "Metode Analisis",
     "Definisi": "Metode statistik non-parametrik (Charles Spearman, 1904) untuk mengukur kekuatan dan arah hubungan antara dua variabel berdasarkan ranking, bukan nilai mentah. Nilai r berkisar -1 (berlawanan sempurna) hingga +1 (searah sempurna).",
     "Konteks": "Digunakan di H1, H3, H5 untuk menguji hubungan antar indikator ekonomi. Library: scipy.stats.spearmanr()."},
    {"Istilah": "Rolling Standard Deviation", "Kategori": "Metode Analisis",
     "Definisi": "Standar deviasi yang dihitung dalam window bergerak (misal 12 bulan). Menunjukkan bagaimana volatilitas berubah seiring waktu — spike menandakan periode ketidakpastian tinggi.",
     "Konteks": "Digunakan di H5 untuk mengukur volatilitas gap IKK dari waktu ke waktu."},
    {"Istilah": "Self-Reinforcing Cycle", "Kategori": "Ekonomi",
     "Definisi": "Siklus yang memperkuat dirinya sendiri — satu kejadian memicu kejadian lain yang memperburuk kondisi awal. Contoh: pelarian modal → tekanan rupiah → suku bunga naik → biaya investasi naik → lebih banyak investor pergi.",
     "Konteks": "Dampak regulatory reversal (H4) dan criminalization risk (H5) terhadap iklim investasi."},
    {"Istilah": "Rate of Change", "Kategori": "Metode Analisis",
     "Definisi": "Persentase perubahan suatu nilai dari satu periode ke periode berikutnya. Mengukur kecepatan dan arah perubahan, bukan level absolut.",
     "Konteks": "Digunakan di H3 untuk mendeteksi lonjakan ICOR tahunan. Library: pandas.pct_change()."},
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

    for idx, row in cat_items.iterrows():
        st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 18px; border-radius:8px; margin-bottom:8px; border-left:3px solid #43A047;">
    <strong style="color:#66BB6A; font-size:1.05rem;">{row['Istilah']}</strong><br>
    <span style="color:#E0E0E0;">{row['Definisi']}</span><br>
    <small style="color:#9E9E9E;">{row['Konteks']}</small>
</div>
""", unsafe_allow_html=True)

    st.markdown("")

# Footer
st.markdown("---")
st.caption(_("Glosarium ini disusun berdasarkan kerangka riset LEUI dan akan terus diperbarui seiring perkembangan analisis."))
