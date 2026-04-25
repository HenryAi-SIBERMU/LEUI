"""
Page 1 — H1: Inconsistency Risk
Analisis inkonsistensi biaya/realisasi investasi antar wilayah sebagai proxy
ketidakpastian hukum daerah.

Causal Chain: Penegakan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi
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

PLOTLY_TEMPLATE = "plotly_dark"
C_ASING = "#42A5F5"
C_DOMESTIK = "#66BB6A"
C_WARN = "#FF9800"
C_DANGER = "#E53935"
C_BG = "#1E1E1E"


def gini_coefficient(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    arr = arr[arr >= 0]
    if len(arr) < 2 or arr.sum() == 0:
        return np.nan
    arr = np.sort(arr)
    n = len(arr)
    idx = np.arange(1, n + 1)
    return (2 * np.sum(idx * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr))


def format_number(val):
    if abs(val) >= 1e6:
        return f"{val/1e6:,.1f}jt"
    if abs(val) >= 1e3:
        return f"{val/1e3:,.1f}rb"
    return f"{val:,.1f}"


# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "final")

@st.cache_data
def load_data():
    df_a = pd.read_csv(os.path.join(DATA, "realisasi_investasi_asing.csv"), parse_dates=["date"])
    df_d = pd.read_csv(os.path.join(DATA, "realisasi_investasi_domestik.csv"), parse_dates=["date"])
    df_i = pd.read_csv(os.path.join(DATA, "icor_nasional.csv"), parse_dates=["date"])
    return df_a, df_d, df_i

df_asing, df_domestik, df_icor = load_data()


# ── Pre-compute ALL numbers for narratives ──
def calc_std_q(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    s = prov_q.groupby("date")["nilai_idr_bn"].std().reset_index()
    s.columns = ["date", "std_dev"]
    s["tipe"] = label
    return s

def calc_gini_q(df, label):
    prov_q = df.groupby([pd.Grouper(key="date", freq="QE"), "provinsi"])["nilai_idr_bn"].sum().reset_index()
    g = prov_q.groupby("date")["nilai_idr_bn"].apply(gini_coefficient).reset_index()
    g.columns = ["date", "gini"]
    g["tipe"] = label
    return g

std_a = calc_std_q(df_asing, "Investasi Asing (PMA)")
std_d = calc_std_q(df_domestik, "Investasi Domestik (PMDN)")
gini_a = calc_gini_q(df_asing, "Investasi Asing (PMA)")
gini_d = calc_gini_q(df_domestik, "Investasi Domestik (PMDN)")

# Aggregate per provinsi
df_all = pd.concat([df_asing.assign(tipe="Asing"), df_domestik.assign(tipe="Domestik")], ignore_index=True)
prov_avg = df_all.groupby("provinsi")["nilai_idr_bn"].mean().sort_values(ascending=True).reset_index()
prov_avg.columns = ["provinsi", "rata_rata"]

# Stats
n_prov_a = df_asing['provinsi'].nunique()
rng_start = df_asing['date'].min().strftime('%Y')
rng_end = df_asing['date'].max().strftime('%Y')

latest_gini_a = gini_a["gini"].dropna().iloc[-1]
latest_gini_d = gini_d["gini"].dropna().iloc[-1]
avg_gini_a = gini_a["gini"].dropna().mean()
avg_gini_d = gini_d["gini"].dropna().mean()

latest_std_a = std_a["std_dev"].iloc[-1]
latest_std_d = std_d["std_dev"].iloc[-1]

# Gini trend (first vs last 4 quarters)
gini_a_early = gini_a["gini"].dropna().head(4).mean()
gini_a_late = gini_a["gini"].dropna().tail(4).mean()
gini_a_change = ((gini_a_late - gini_a_early) / gini_a_early * 100) if gini_a_early > 0 else 0

# Province top/bottom
prov_top1 = prov_avg.iloc[-1]
prov_top2 = prov_avg.iloc[-2]
prov_top3 = prov_avg.iloc[-3]
prov_bot1 = prov_avg.iloc[0]
prov_bot2 = prov_avg.iloc[1]
prov_bot3 = prov_avg.iloc[2]
ratio_top_bot = prov_top1['rata_rata'] / prov_bot1['rata_rata'] if prov_bot1['rata_rata'] > 0 else 0

# Top 5 prov share
total_inv = prov_avg['rata_rata'].sum()
top5_share = prov_avg.tail(5)['rata_rata'].sum() / total_inv * 100 if total_inv > 0 else 0
bot10_share = prov_avg.head(10)['rata_rata'].sum() / total_inv * 100 if total_inv > 0 else 0

# ICOR
_df_icor_clean = df_icor.dropna(subset=['icor_pma', 'icor_pmdn'])
icor_first = _df_icor_clean['icor_pma'].iloc[0] if len(_df_icor_clean) > 0 else 0
icor_last = _df_icor_clean['icor_pma'].iloc[-1] if len(_df_icor_clean) > 0 else 0
icor_d_first = _df_icor_clean['icor_pmdn'].iloc[0] if len(_df_icor_clean) > 0 else 0
icor_d_last = _df_icor_clean['icor_pmdn'].iloc[-1] if len(_df_icor_clean) > 0 else 0
icor_year_first = _df_icor_clean['date'].iloc[0].strftime('%Y') if len(_df_icor_clean) > 0 else '—'
icor_year_last = _df_icor_clean['date'].iloc[-1].strftime('%Y') if len(_df_icor_clean) > 0 else '—'
icor_pma_trend = ((icor_last - icor_first) / icor_first * 100) if icor_first > 0 else 0

# ── Load Legal datasets ──
_ma_yearly_path = os.path.join(DATA, "putusan_ma_yearly.csv")
_ma_osint_path = os.path.join(DATA, "..", "raw", "putusan_ma_osint.csv")
_reg_h1_path = os.path.join(DATA, "regulasi_h1_yearly.csv")
_churn_path = os.path.join(DATA, "regulatory_churn_rate.csv")
_ma_stat_path = os.path.join(DATA, "laporan_ma_statistik.csv")
_sipp_durasi_path = os.path.join(DATA, "sipp_durasi_distribution.csv")
_sipp_pn_path = os.path.join(DATA, "sipp_pn_distribution.csv")
_sipp_yearly_path = os.path.join(DATA, "sipp_yearly.csv")
_sipp_monthly_path = os.path.join(DATA, "sipp_wanprestasi_monthly.csv")
_sipp_monthly_pn_path = os.path.join(DATA, "sipp_monthly_per_pn.csv")
_sipp_boxplot_path = os.path.join(DATA, "sipp_boxplot_stats.csv")

_total_ma = 0
_df_ma_osint = None
if os.path.exists(_ma_osint_path):
    _df_ma_osint_raw = pd.read_csv(_ma_osint_path)
    _total_ma = len(_df_ma_osint_raw)  # Sinkronisasi dengan jumlah riil OSINT
    
    if "title" in _df_ma_osint_raw.columns and "snippet" in _df_ma_osint_raw.columns:
        _df_ma_osint = _df_ma_osint_raw[["title", "snippet", "url"]].copy()
        _df_ma_osint.columns = ["Judul Putusan / Pengadilan", "Kutipan Amar Putusan (Pangkal Sengketa)", "Link Direktori MA"]

_df_ma_yr = None
if os.path.exists(_ma_yearly_path):
    _df_ma_yr = pd.read_csv(_ma_yearly_path)

_total_reg = 0
_berlaku = 0
_dicabut = 0
_df_reg_h1 = None
if os.path.exists(_reg_h1_path):
    _df_reg_h1 = pd.read_csv(_reg_h1_path)
    _df_reg_h1 = _df_reg_h1[_df_reg_h1['year'] >= 2000]
    _total_reg = int(_df_reg_h1['jumlah'].sum())
    _berlaku = int(_df_reg_h1[_df_reg_h1['status'] == 'berlaku']['jumlah'].sum()) if 'status' in _df_reg_h1.columns else _total_reg
    _dicabut = _total_reg - _berlaku

_df_churn = None
if os.path.exists(_churn_path):
    _df_churn = pd.read_csv(_churn_path)
    _df_churn = _df_churn[_df_churn['year'] >= 2000]

_df_ma_stat = None
_reversal_rate = 0
_clearance_rate = 0
_ma_total_perkara = 0
_ma_dikabulkan = 0
if os.path.exists(_ma_stat_path):
    _df_ma_stat = pd.read_csv(_ma_stat_path)
    if not _df_ma_stat.empty:
        _reversal_rate = _df_ma_stat.iloc[0].get('reversal_rate_pct', 0)
        _clearance_rate = _df_ma_stat.iloc[0].get('clearance_rate_pct', 0)
        _ma_total_perkara = int(_df_ma_stat.iloc[0].get('total_perkara', 0))
        _ma_dikabulkan = int(_df_ma_stat.iloc[0].get('dikabulkan', 0))

# Load SIPP All-PN for raw totals
_sipp_all_pn_path = os.path.join(DATA, "sipp_all_pn_nasional.csv")
_sipp_raw_total = 0
_sipp_pn_count = 0
if os.path.exists(_sipp_all_pn_path):
    _df_sipp_all = pd.read_csv(_sipp_all_pn_path)
    _sipp_raw_total = int(_df_sipp_all['total_sengketa'].sum())
    _sipp_pn_count = len(_df_sipp_all)

_df_sipp_durasi = None
if os.path.exists(_sipp_durasi_path):
    _df_sipp_durasi = pd.read_csv(_sipp_durasi_path)

_df_sipp_pn = None
if os.path.exists(_sipp_pn_path):
    _df_sipp_pn = pd.read_csv(_sipp_pn_path)

_df_sipp_yearly = None
_total_sipp = 0
if os.path.exists(_sipp_yearly_path):
    _df_sipp_yearly = pd.read_csv(_sipp_yearly_path)
    _total_sipp = int(_df_sipp_yearly['total_perkara'].sum())

# Load raw SIPP corporate data for status analysis & table display
_sipp_corp_path = os.path.join(DATA, "sipp_corporate_wanprestasi.csv")
_df_sipp_corp = None
_sipp_status_desc = "tercatat di pengadilan negeri"
if os.path.exists(_sipp_corp_path):
    _df_sipp_corp = pd.read_csv(_sipp_corp_path)
    if 'Status Perkara' in _df_sipp_corp.columns:
        _status_counts = _df_sipp_corp['Status Perkara'].value_counts()
        _status_parts = [f"{v:,} berstatus '{k}'" for k, v in _status_counts.head(3).items()]
        _sipp_status_desc = "tercatat di pengadilan negeri (" + ", ".join(_status_parts) + ", dll)"
    _total_sipp = len(_df_sipp_corp)  # Sinkronisasi dengan data riil
_sipp_filter_pct = (_total_sipp / _sipp_raw_total * 100) if _sipp_raw_total > 0 else 0

_df_sipp_monthly = None
if os.path.exists(_sipp_monthly_path):
    _df_sipp_monthly = pd.read_csv(_sipp_monthly_path)

_df_sipp_monthly_pn = None
if os.path.exists(_sipp_monthly_pn_path):
    _df_sipp_monthly_pn = pd.read_csv(_sipp_monthly_pn_path)

_df_sipp_boxplot = None
if os.path.exists(_sipp_boxplot_path):
    _df_sipp_boxplot = pd.read_csv(_sipp_boxplot_path)


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title(_("H1: Zona Merah Investasi (Inkonsistensi Area)"))
subtitle = _("Uang hanya berputar di segelintir provinsi karena penegakan hukum yang rentan dan berbeda-beda.")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander(_("🔍 Metodologi"), expanded=False):
    st.markdown(_("""
    **Alur Kausalitas (Law & Economics):**
    `Penegakan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi`

    Ketidakpastian tata hukum diterjemahkan oleh investor sebagai risiko. Risiko tersebut akhirnya dihargai dalam wujud permintaan keuntungan yang lebih tinggi (*risk premium*), penundaan investasi, hingga keputusan untuk memusatkan investasi (konsentrasi ekstrem) di \"safe haven\".
    
    Bentuk risiko H1 yang paling utama dianalisis dalam dasbor ini meliputi:
    - Ketidakkonsistenan putusan atau tindakan hukum untuk kasus yang serupa.
    - Proses peradilan bisnis yang panjang, mahal, dan tumpang tindih.
    - Perubahan regulasi atau pencabutan izin investasi secara mendadak.

    **Variabel Hukum (X):**
    - Volume putusan MA terkait sengketa perdata bisnis per tahun (Data Mining OSINT).
    - Reversal Rate & Clearance Rate Mahkamah Agung (Laporan Tahunan MA).
    - Status churn regulasi esensial daerah/pusat yang dicabut/diubah (Pasal.id).
    - Durasi & volume sengketa pengadilan negeri (Scraping SIPP PN).
    
    **Dampak Ekonomi (Y):**
    - Gini Coefficient volatilitas distribusi investasi antar provinsi (Ketimpangan absolut).
    - Standard Deviation sebaran investasi (Konsentrasi Spasial).
    - Distribusi Top/Bottom provinsi (Konsentrasi Modal).
    - ICOR Nasional (Efisiensi & Biaya Ekonomi/Keputusan).
    """))

# ── Intro Narrative ──
st.markdown(f"""
<div style="background-color: #2F0A28; padding: 30px; border-radius: 10px; border-left: 8px solid #FF3D00; text-align: center; margin-bottom: 20px;">
    <h2 style="color: #FF8A65; font-size: 2rem; margin-bottom: 15px;">5 Provinsi Menguasai {top5_share:.0f}% Investasi Indonesia.<br>Sisanya? Ditinggalkan.</h2>
    <p style="color: #E0E0E0; font-size: 1.1rem;">Ketidakpastian aturan dan sengketa hukum yang tak berujung membuat investor takut menanam modal di daerah berkembang.</p>
</div>
""", unsafe_allow_html=True)

intro = _("""Inkonsistensi hukum bukan lagi sebatas wacana yuridis, melainkan *driver* utama ketimpangan struktural ekonomi Indonesia. Analisis data realisasi **{start}–{end}** pada **{n_prov} provinsi** memperlihatkan bagaimana tingginya risiko sengketa perdata (tercatat **{tot_ma} putusan MA bisnis**, dengan reversal rate **{rev_rate:.2f}%**) dan tumpang tindih aturan (sedikitnya **{tot_dicabut} regulasi daerah/pusat dicabut/diubah**) serta **{tot_sipp} sengketa PN** menciptakan *barrier to entry* tak kasat mata. 

Investor merespons beban ketidakpastian ini secara defensif dengan memusatkan modal mereka ke segelintir "safe haven" yang terbukti aman. Hasilnya, Gini rasio investasi asing (PMA) meledak ke **{gini_a:.3f}** dan PMDN menembus **{gini_d:.3f}**—angka yang mengonfirmasi ketimpangan absolut. Terbukti, **5 provinsi teratas sanggup menyedot {top5:.1f}% investasi nasional**, membiarkan **10 provinsi terbawahnya memperebutkan remah-remah {bot10:.1f}%**.""")
st.markdown(
    intro.format(
        start=rng_start, end=rng_end, n_prov=n_prov_a, 
        tot_ma=_total_ma, rev_rate=_reversal_rate, tot_dicabut=_dicabut,
        tot_sipp=_total_sipp,
        gini_a=latest_gini_a, gini_d=latest_gini_d,
        top5=top5_share, bot10=bot10_share
    ),
    unsafe_allow_html=True
)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ── Overview KPI Cards (Traffic Light) ──
col1, col2, col3 = st.columns(3)
with col1:
    hukum_status = "BURUK" if _reversal_rate > 10 else "AWAS"
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid #E53935; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">KONSISTENSI HUKUM</h4>
        <h2 style="color: #E53935; margin: 0; font-size: 1.8rem;">{hukum_status}</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;"><b>{_reversal_rate:.1f}%</b> putusan pengadilan terbukti dibatalkan oleh MA.</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> Laporan Tahunan MA mencatat <b>{_ma_total_perkara:,}</b> sengketa perdata bisnis kasasi. MA membatalkan <b>{_ma_dikabulkan:,}</b> putusan dari pengadilan bawah.<br><i>(Kalkulasi: {_ma_dikabulkan:,} ÷ {_ma_total_perkara:,} = {_reversal_rate:.1f}%)</i>
        </p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid #E53935; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">STABILITAS ATURAN</h4>
        <h2 style="color: #E53935; margin: 0; font-size: 1.8rem;">TIDAK STABIL</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;"><b>{_dicabut}</b> regulasi bisnis / daerah rentan dicabut mendadak.</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> Dari total <b>{_total_reg:,}</b> regulasi esensial daerah/pusat yang terbit, sebanyak <b>{_dicabut:,}</b> aturan terbukti berakhir dicabut, dibatalkan MK/MA, atau direvisi mendadak di tengah jalan.
        </p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    g_color = '#E53935' if latest_gini_a > 0.4 else '#4CAF50'
    g_status = 'SANGAT TIMPANG' if latest_gini_a > 0.6 else 'TIMPANG' if latest_gini_a > 0.4 else 'AMAN'
    g_icon = '' if latest_gini_a > 0.4 else ''
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {g_color}; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">DISTRIBUSI DAERAH</h4>
        <h2 style="color: {g_color}; margin: 0; font-size: 1.8rem;">{g_icon} {g_status}</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;">Gini indeks <b>{latest_gini_a:.2f}</b>, modal hanya menumpuk di pusat.</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> Skala 0 (Merata) sampai 1 (Sangat Timpang). Angka {latest_gini_a:.2f} membuktikan 5 provinsi teratas menyedot <b>{top5_share:.0f}%</b> total investasi asing, membiarkan 10 provinsi terbawah memperebutkan sisa <b>{bot10_share:.0f}%</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with st.expander(_("Lihat Rincian Angka Mentah (Total Perkara)"), expanded=False):
    c1, c2 = st.columns(2)
    c1.metric("Putusan MA Kasasi (OSINT)", f"{_total_ma:,}")
    c2.metric("Sengketa Wanprestasi di PN (SIPP)", f"{_total_sipp:,}")
    
    st.markdown(f"""
    <div style="background-color: #2D2D2D; padding: 12px 15px; border-radius: 5px; border-left: 4px solid #FFA000; font-size: 0.85rem; color: #E0E0E0; margin-top: 10px;">
        <b>💡 Kenapa Perbedaan Angkanya Jauh Sekali?</b><br>
        <b>Kedua dataset sudah difilter sesuai taksonomi riset:</b>
        <ul style="margin: 8px 0;">
            <li><b>{_total_sipp:,} kasus PN (SIPP)</b> — difilter pada <code>Klasifikasi Perkara = Wanprestasi</code> dari portal SIPP Pengadilan Negeri. Angka besar ini wajar karena mencakup <i>seluruh sengketa wanprestasi</i> yang masuk di <b>level pengadilan tingkat pertama</b> (volume masuk).</li>
            <li><b>{_total_ma:,} kasus MA (OSINT)</b> — dikurasi dari Direktori Putusan MA via Google Dorking dengan filter: <i>"wanprestasi+investasi", "perizinan+batal", "pencabutan izin tambang"</i>. Angka kecil ini karena hanya putusan tingkat <b>Kasasi/PK</b> (puncak hierarki peradilan) yang terekspos publik dan lolos filter spesifik.</li>
        </ul>
        Kesimpulan: Perbedaan ini mencerminkan <b>piramida alami peradilan Indonesia</b> — dari puluhan ribu sengketa yang masuk di bawah, hanya segelintir yang naik sampai ke puncak MA.
    </div>
    """, unsafe_allow_html=True)

    # Tabel raw SIPP
    if _df_sipp_corp is not None:
        _display_cols = [c for c in ['Nomor Perkara', 'Tanggal Daftar', 'Klasifikasi Perkara', 'Status Perkara', 'Lama Proses', 'Pengadilan'] if c in _df_sipp_corp.columns]
        if _display_cols:
            st.markdown("---")
            st.markdown("**📋 Sampel Data Mentah SIPP (Wanprestasi Korporasi):**")
            st.dataframe(_df_sipp_corp[_display_cols].head(200), use_container_width=True, hide_index=True)
            st.caption(f"📁 **Sumber File:** `data/final/sipp_corporate_wanprestasi.csv` — Menampilkan 200 dari {len(_df_sipp_corp):,} baris")


# ══════════════════════════════════════════════════════════
# ═══════════ LAYER X: VARIABEL HUKUM ═════════════════════
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.subheader("1. Fakta Penyebab: Sistem Hukum Indonesia Sangat Membingungkan Investor")

_sipp_bullet = f"Lebih dari <b>{_total_sipp:,} kasus sengketa wanprestasi korporasi</b> {_sipp_status_desc}."
st.markdown(f'''
<ul style="font-size: 1.1rem; line-height: 1.6; color: #E0E0E0; background-color: #261313; padding: 25px 40px; border-radius: 10px; border-left: 5px solid #FF5722;">
    <li><b>Pengadilan Sering Berubah Pikiran:</b> Mahkamah Agung membalikkan <b>{_reversal_rate:.1f}%</b> putusan pengadilan perdata yang lebih rendah. Kontrak bisnis rentan dibatalkan kapan saja.</li>
    <li><b>Aturan yang Mudah Hangus:</b> Sedikitnya <b>{_dicabut} regulasi bisnis esensial</b> (daerah/pusat) dicabut atau direvisi mendadak dalam periode ini.</li>
    <li><b>Sengketa Hukum yang Membludak:</b> {_sipp_bullet}</li>
</ul>
''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 1.1 YUDISIAL (HUKUM) — ENRICHED
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.1 Sengketa Tak Berujung di Mahkamah Agung"))
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Agregasi Putusan Direktori MA + Laporan Tahunan MA (Variabel X1)</span>', unsafe_allow_html=True)

ma_narrative = _("""Menggunakan metode **Data Mining Putusan Mahkamah Agung** untuk mengekstrak dan mengagregasi volume sengketa perdata bisnis (wanprestasi, investasi, lisensi). Secara spesifik, dalam **Laporan Tahunan MA terbaru (Kamar Perdata)** tercatat beban perkara perdata sebanyak **{ma_total:,} kasus**, di mana **{ma_kabulkan:,} putusan kasasi/PK dikabulkan**. 

Artinya, **{rev_rate:.2f}% (*Reversal Rate*)** dari total putusan pengadilan tinggi/negeri sebelumnya telah dibatalkan atau dibalikkan oleh Mahkamah Agung. Angka >10% ini menjadi sinyal inkonsistensi sistemik. Bagi investor, fakta empiris ini membuktikan ketakutan terbesar mereka: kemenangan sengketa kontrak bisnis di level pengadilan pertama sangat rentan dianulir sewaktu-waktu di tahap akhir (kasasi).""")

ma_src = _("Berdasarkan scraping <code>putusan3.mahkamahagung.go.id</code> (Filter: Perdata Khusus, Bisnis, Investasi) + <code>Laporan Tahunan MA 2023-2024</code>.")
st.markdown(ma_narrative.format(rev_rate=_reversal_rate, clear_rate=_clearance_rate, ma_total=_ma_total_perkara, ma_kabulkan=_ma_dikabulkan) + f"\n\n<small><b>Sumber:</b> {ma_src}</small>", unsafe_allow_html=True)

if _df_ma_yr is not None:
    max_val = _df_ma_yr["total_putusan"].max()
    colors = ['#E53935' if val == max_val else '#424242' for val in _df_ma_yr["total_putusan"]]
    
    _fig_ma = go.Figure(data=[
        go.Bar(
            x=_df_ma_yr["year"], 
            y=_df_ma_yr["total_putusan"], 
            marker_color=colors,
            hovertemplate="<b>Tahun: %{x}</b><br>Sengketa Kasasi MA: <b>%{y} Kasus</b><extra></extra>"
        )
    ])
    _fig_ma.update_layout(
        template=PLOTLY_TEMPLATE, height=350, margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text="Lonjakan Sengketa Bisnis di Mahkamah Agung", font=dict(color="#E0E0E0", size=16)),
        yaxis=dict(title="", showgrid=True, gridcolor="#333"),
        xaxis=dict(title="")
    )
    if _df_ma_yr.shape[0] > 0:
        peak_year = _df_ma_yr.loc[_df_ma_yr["total_putusan"] == max_val, "year"].values[0]
        _fig_ma.add_annotation(
            x=peak_year, y=max_val,
            text="Puncak Ketidakpastian",
            showarrow=True, arrowhead=1, arrowcolor="#FF3D00", ax=0, ay=-40, font=dict(color="#FF3D00")
        )
    st.plotly_chart(_fig_ma, use_container_width=True)
    
    st.markdown(f"""
    <div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #AB47BC; margin-bottom: 20px; margin-top: 5px;">
        Data direktori Mahkamah Agung mencatat adanya <strong>{_total_ma} sengketa perdata bisnis</strong> yang bermuara hingga kasasi. Reversal rate <strong>{_reversal_rate:.2f}%</strong> mengonfirmasi bahwa <em>procedural uncertainty</em> bukan asumsi—melainkan fakta terukur dari data peradilan.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(_("Lihat Bukti Putusan: Jejak Digital Sengketa Aktual di MA"), expanded=False):
        if _df_ma_osint is not None:
            st.dataframe(_df_ma_osint, use_container_width=True, hide_index=True)
            st.caption("Sampel data diekstraksi dari putusan3.mahkamahagung.go.id melalui Dorking OSINT")
        else:
            st.dataframe(_df_ma_yr, use_container_width=True, hide_index=True)

# Laporan MA Statistik table
if _df_ma_stat is not None:
    with st.expander(_("Lihat Data: Laporan Tahunan MA (Statistik Performa)"), expanded=False):
        st.dataframe(_df_ma_stat, use_container_width=True, hide_index=True)
        st.caption("📁 **Sumber File:** `data/final/laporan_ma_statistik.csv`")


# ══════════════════════════════════════════════════
# 1.2 REGULASI (HUKUM) — ENRICHED with churn rate
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.2 Aturan Bisnis Sering Dicabut / Diganti Mendadak"))
st.markdown('<span style="background:#0D47A1;color:#BBDEFB;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Regulatory Churn Test + Lifecycle Analysis (Variabel X2)</span>', unsafe_allow_html=True)

reg_narrative = _("""Menggunakan metode **Regulatory Churn Test** untuk mengukur tingkat ketidakpastian produk hukum yang esensial bagi iklim usaha. Kami melacak siklus hidup puluhan regulasi kunci (daerah maupun pusat) yang mengatur izin usaha, perpajakan lokal, dan tata ruang.

Grafik pertama membandingkan regulasi mana yang bertahan (berlaku) melawan regulasi yang sudah layu sebelum berkembang (dicabut, dibatalkan MA/MK, atau direvisi). Grafik kedua memperlihatkan **tren Regulatory Churn Rate nasional** — persentase regulasi bisnis yang dicabut/diubah setiap tahunnya. Lonjakan churn rate di tahun-tahun tertentu mencerminkan masa-masa di mana *shock cost* bagi investor meledak: aturan yang ditandatangani hari ini bisa saja ilegal esok hari.""")

reg_src = _("Ekstraksi status dari database regulasi Pasal.id & JDIH (Dataset Bappenas).")
st.markdown(reg_narrative + f"\n\n<small><b>Sumber:</b> {reg_src}</small>", unsafe_allow_html=True)

if _df_reg_h1 is not None:
    _fig_reg = px.bar(
        _df_reg_h1, x="year", y="jumlah", color="status",
        color_discrete_map={"berlaku": "#555555", "tidak_berlaku": "#E53935"},
        template=PLOTLY_TEMPLATE, barmode="group",
        labels={"year": "Tahun", "jumlah": "Jumlah Regulasi", "status": ""}
    )
    _fig_reg.update_layout(
        height=350, margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified",
        title=dict(text="Perbandingan Aturan yang Layu Sebelum Berkembang", font=dict(color="#E0E0E0", size=16)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    _fig_reg.update_xaxes(range=[2000, 2024])
    st.plotly_chart(_fig_reg, use_container_width=True)
    
    with st.expander(_("Lihat Data: Regulasi H1 Yearly"), expanded=False):
        st.dataframe(_df_reg_h1, use_container_width=True, hide_index=True)
        st.caption("📁 **Sumber File:** `data/final/regulasi_h1_yearly.csv`")

# Churn Rate Line Chart (NEW)
if _df_churn is not None:
    _fig_churn = go.Figure()
    _fig_churn.add_trace(go.Scatter(
        x=_df_churn["year"], y=_df_churn["churn_rate"],
        mode="lines+markers", name="Tingkat Aturan Dicabut (%)",
        line=dict(color="#FF3D00", width=4), marker=dict(size=8),
        fill="tozeroy", fillcolor="rgba(255,61,0,0.1)"
    ))
    _fig_churn.add_trace(go.Bar(
        x=_df_churn["year"], y=_df_churn["total"],
        name="Total Regulasi Terbit", marker_color="#5C5C5C",
        yaxis="y2", opacity=0.85
    ))
    _fig_churn.update_layout(
        template=PLOTLY_TEMPLATE, height=400,
        title=dict(text="Tren Pencabutan Aturan Mendadak (Regulatory Churn Rate)", font=dict(color="#E0E0E0", size=16)),
        yaxis=dict(title="Persentase Dicabut (%)", side="left", overlaying="y2", gridcolor="#333"),
        yaxis2=dict(title="", side="right", showgrid=False, showticklabels=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified",
        hoverlabel=dict(namelength=-1)
    )
    _fig_churn.update_xaxes(range=[2000, 2024])
    if _df_churn.shape[0] > 1:
        _dfs = _df_churn.sort_values("churn_rate", ascending=False)
        peak1 = _dfs.iloc[0]
        peak2 = _dfs.iloc[1]
        
        ax_p1 = 40 if peak1["year"] < 2005 else -40
        ax_p2 = 40 if peak2["year"] < 2005 else -40

        _fig_churn.add_annotation(
            x=peak1["year"], y=peak1["churn_rate"],
            text=f"Puncak Pencabutan:<br>{int(peak1['tidak_berlaku'])} dari {int(peak1['total'])} Aturan Batal", 
            showarrow=True, arrowhead=1, ax=ax_p1, ay=35, font=dict(color="#FF3D00", weight="bold"), align="center"
        )
        
        # Tambahan Data Storytelling di Background
        _fig_churn.add_hrect(y0=0, y1=10, fillcolor="green", opacity=0.08, layer="below", line_width=0)
        _fig_churn.add_hline(y=10, line_dash="dash", line_color="#E53935", 
                             annotation_text="Batas Wajar Maksimal (<10%)", annotation_position="bottom right", 
                             annotation_font_color="#EF9A9A", annotation_font_size=11)
        
        # Anotasi lonjakan kedua (Faktual data)
        _fig_churn.add_annotation(
            x=peak2["year"], y=peak2["churn_rate"],
            text=f"Lonjakan Sekunder:<br>{int(peak2['tidak_berlaku'])} dari {int(peak2['total'])} Aturan Batal", 
            showarrow=True, arrowhead=1, ax=ax_p2, ay=-35, font=dict(color="#FF9800", size=12), align="center"
        )

    st.plotly_chart(_fig_churn, use_container_width=True)
    
    st.markdown(f"""
    <div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #E53935; margin-bottom: 20px; margin-top: 5px;">
        Dari <strong>{_total_reg} regulasi kunci</strong> tingkat daerah dan pusat yang memengaruhi iklim usaha (H1), sebanyak <strong>{_dicabut} aturan berakhir dicabut, dibatalkan, atau direvisi</strong>. Data churn rate nasional menunjukkan lonjakan pencabutan tertinggi di era reformasi dan transisi regulasi daerah, menghancurkan horizon perencanaan jangka panjang bagi investor.
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_("Lihat Data: Regulatory Churn Rate Nasional"), expanded=False):
        st.dataframe(_df_churn, use_container_width=True, hide_index=True)
        st.caption("📁 **Sumber File:** `data/final/regulatory_churn_rate.csv`")


# ══════════════════════════════════════════════════
# 1.3 SIPP — Durasi & Volume Sengketa PN (NEW!)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.3 Proses Hukum dan Sengketa Bisnis yang Lamban"))
st.markdown('<span style="background:#E65100;color:#FFE0B2;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Scraping SIPP Pengadilan Negeri (Variabel X3)</span>', unsafe_allow_html=True)

sipp_narrative = _("""Menggunakan metode **Macro-Level Legal Proxy** dengan meng-*crawl* **Sistem Informasi Penelusuran Perkara (SIPP)** dari **{pn_count} Pengadilan Negeri** se-Indonesia secara massal (OSINT). Dari total **{raw_total:,} perkara wanprestasi** mentah yang berhasil diekstraksi, diterapkan **Corporate Taxonomy Filter** (menyaring hanya perkara yang melibatkan PT, CV, Koperasi, Bank, Yayasan, atau Pemerintah) sehingga diperoleh **{tot_sipp:,} perkara korporasi bersih** (~{filter_pct:.1f}%).

Metodologi ini selaras dengan pendekatan *World Bank Ease of Doing Business* parameter *Enforcing Contracts*: volume & durasi sengketa kontrak bisnis di pengadilan negeri digunakan sebagai **indikator substitusi (proxy)** kualitas infrastruktur Kepastian Hukum suatu wilayah. Semakin tinggi volume dan semakin lama durasi rata-rata penyelesaian, semakin besar **Biaya Transaksi (hidden cost)** yang harus ditanggung investor.""")

sipp_src = _("Scraping massal <code>sipp.[36-PN].go.id</code> — Corporate Taxonomy Filter (PT/CV/Bank/Pemerintah).")
st.markdown(sipp_narrative.format(tot_sipp=_total_sipp, raw_total=_sipp_raw_total, pn_count=_sipp_pn_count, filter_pct=_sipp_filter_pct) + f"\n\n<small><b>Sumber:</b> {sipp_src}</small>", unsafe_allow_html=True)

# ── DATA TABLE: Sampel Data Korporasi yang Telah Difilter ──
_corp_data_path = os.path.join(DATA, "sipp_corporate_wanprestasi.csv")
if os.path.exists(_corp_data_path):
    _df_corp_sample = pd.read_csv(_corp_data_path)
    _display_cols = ['Nomor Perkara', 'Tanggal Daftar', 'Para Pihak', 'Status Perkara', 'Pengadilan', 'durasi_hari']
    _available_cols = [c for c in _display_cols if c in _df_corp_sample.columns]
    with st.expander(_("Lihat Data: Hasil Corporate Taxonomy Filter ({:,} perkara korporasi dari {:,} mentah)".format(len(_df_corp_sample), _sipp_raw_total)), expanded=False):
        st.dataframe(_df_corp_sample[_available_cols].head(500), use_container_width=True, hide_index=True)
        st.markdown("<small style='color:#888;'>Menampilkan 500 dari {:,} perkara. Filter: PT, CV, Koperasi, Bank, Yayasan, Pemerintah.<br>📁 <b>Sumber File:</b> <code>data/final/sipp_corporate_wanprestasi.csv</code></small>".format(len(_df_corp_sample)), unsafe_allow_html=True)

# Durasi Distribution Chart
if _df_sipp_durasi is not None and "durasi_hari" in _df_sipp_durasi.columns:
    total_cases = _df_sipp_durasi["jumlah"].sum()
    cum_sum = _df_sipp_durasi["jumlah"].cumsum()
    median_hari = _df_sipp_durasi.loc[cum_sum >= total_cases/2, "durasi_hari"].min() if total_cases > 0 else 0
    
    _fig_dur = px.bar(
        _df_sipp_durasi, x="durasi_hari", y="jumlah",
        color_discrete_sequence=["#FF9800"],
        template=PLOTLY_TEMPLATE,
        labels={"durasi_hari": "Lama Proses (Hari)", "jumlah": "Frekuensi Perkara"}
    )
    _fig_dur.update_layout(
        height=350, margin=dict(l=20, r=20, t=60, b=20),
        title=dict(text="Lama Waktu Tunggu Sengketa (Makin Lama Makin Mahal)", font=dict(color="#E0E0E0", size=16)),
        xaxis=dict(title="Durasi Proses Hukum (Hari)", range=[0, min(1000, _df_sipp_durasi["durasi_hari"].max())], gridcolor="#333"),
        yaxis=dict(title="", gridcolor="#333")
    )
    if median_hari > 0:
        _fig_dur.add_vline(x=median_hari, line_dash="dash", line_color="#E53935", line_width=3)
        _fig_dur.add_annotation(
            x=median_hari + 1, y=_df_sipp_durasi["jumlah"].max() * 0.85,
            text=f"Rata-rata modal mandek<br>hingga {median_hari} Hari",
            showarrow=False, font=dict(color="#FF3D00", size=14, weight="bold"), xanchor="left"
        )
                           
    st.plotly_chart(_fig_dur, use_container_width=True)
    
    with st.expander(_("Lihat Data: Distribusi Durasi (Harian)"), expanded=False):
        st.dataframe(_df_sipp_durasi, use_container_width=True, hide_index=True)
        st.caption("📁 **Sumber File:** `data/final/sipp_durasi_distribution.csv`")

# ── CHART: Grouped Bar — Volume Sengketa per PN per Bulan ──
if _df_sipp_monthly_pn is not None and not _df_sipp_monthly_pn.empty:
    st.caption(_("Volume Sengketa Korporasi per Pengadilan Negeri — Tren Bulanan"))
    _fig_grouped = px.bar(
        _df_sipp_monthly_pn, x="YearMonth", y="jumlah", color="Pengadilan",
        barmode="group",
        text="jumlah",
        color_discrete_sequence=["#FF7043", "#FFA726", "#FFCC80"],
        template=PLOTLY_TEMPLATE,
        labels={"YearMonth": "Bulan", "jumlah": "Jumlah Perkara", "Pengadilan": "Pengadilan Negeri"},
        hover_data={"avg_durasi": ":.1f"}
    )
    _fig_grouped.update_traces(textposition='outside', textfont_size=10)
    _fig_grouped.update_layout(
        height=400, margin=dict(l=20, r=20, t=60, b=20),
        title=dict(text="Lonjakan Sengketa Bulanan (Sangat Timpang Antar Daerah)", font=dict(color="#E0E0E0", size=16)),
        xaxis=dict(type='category', title="", showgrid=False),
        yaxis=dict(title="", gridcolor="#333"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    if not _df_sipp_monthly_pn.empty:
        max_row = _df_sipp_monthly_pn.loc[_df_sipp_monthly_pn["jumlah"].idxmax()]
        _fig_grouped.add_annotation(
            x=max_row["YearMonth"], y=max_row["jumlah"],
            text=f"Beban Perkara Ekstrem<br>({max_row['Pengadilan']})",
            showarrow=True, arrowhead=1, ax=-50, ay=-40, font=dict(color="#FF9800", size=13, weight="bold")
        )
    st.plotly_chart(_fig_grouped, use_container_width=True)
    
    with st.expander(_("Lihat Data: Volume per PN per Bulan"), expanded=False):
        st.dataframe(_df_sipp_monthly_pn, use_container_width=True, hide_index=True)
        st.caption("📁 **Sumber File:** `data/final/sipp_monthly_per_pn.csv`")

# ── CHART: Horizontal Bar — Sebaran Sengketa Korporasi 40 PN Nasional ──
_all_pn_path = os.path.join(DATA, "sipp_all_pn_nasional.csv")
_df_all_pn = None
if os.path.exists(_all_pn_path):
    _df_all_pn = pd.read_csv(_all_pn_path)

if _df_all_pn is not None and not _df_all_pn.empty:
    _n_pn = len(_df_all_pn)
    _total_all = int(_df_all_pn['total_sengketa'].sum())
    _df_all_sorted = _df_all_pn.sort_values("total_sengketa", ascending=True).tail(10) # HANYA TOP 10 BIAR GAK SCROLL!
    
    colors = ['#E53935' if val == _df_all_sorted["total_sengketa"].max() else '#424242' for val in _df_all_sorted["total_sengketa"]]
    _fig_all_pn = go.Figure(go.Bar(
        x=_df_all_sorted["total_sengketa"], y=_df_all_sorted["PN_norm"], orientation="h",
        text=_df_all_sorted["total_sengketa"].apply(lambda x: f"{x:,}"),
        marker_color=colors, textposition='outside', textfont_size=12,
        hovertemplate="<b>%{y}</b><br>Jumlah Perkara Macet: <b>%{x} Kasus</b><extra></extra>"
    ))
    _fig_all_pn.update_layout(
        height=400, margin=dict(l=20, r=80, t=40, b=20),
        title=dict(text="10 Pengadilan Paling 'Macet' (Penumpukan Kasus Tertinggi)", font=dict(color="#E0E0E0", size=16)),
        xaxis=dict(title="", showgrid=False, showticklabels=False),
        yaxis=dict(title="", tickfont=dict(size=12))
    )
    st.plotly_chart(_fig_all_pn, use_container_width=True)

    _top_pn = _df_all_pn.sort_values("total_sengketa", ascending=False).iloc[0]
    _top_pn_name = _top_pn["PN_norm"]
    _top_pn_val = int(_top_pn["total_sengketa"])
    _avg_others = int(_df_all_pn[_df_all_pn["PN_norm"] != _top_pn_name]["total_sengketa"].mean()) if _n_pn > 1 else 0
    _deep_scrape_count = len(_df_all_pn[_df_all_pn["sources"].str.contains("Deep Scrape", na=False)])
    _enriched_count = len(_df_all_pn[_df_all_pn["sources"].str.contains("Enriched", na=False)])
    _osint_count = len(_df_all_pn[_df_all_pn["sources"].str.contains("OSINT", na=False)])
    
    st.markdown(f"""
    <div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #FF9800; margin-bottom: 20px; margin-top: 10px;">
        <b>Interpretasi:</b> Data dari <strong>{_n_pn} Pengadilan Negeri</strong> di seluruh Indonesia dikumpulkan dari 3 sumber: (1) <em>Deep Scrape</em> SIPP — {_total_sipp:,} perkara korporasi dari {_deep_scrape_count} PN utama, (2) <em>Enriched Scrape</em> — data tambahan dari {_enriched_count} PN, (3) <em>OSINT Detection</em> — {_osint_count} PN teridentifikasi via Google DORK. Konsentrasi beban perkara yang <strong>sangat tidak merata</strong> ({_top_pn_name} = {_top_pn_val:,} vs rata-rata PN lain ~{_avg_others:,}) mengkonfirmasi adanya <strong>disparitas infrastruktur peradilan</strong> yang menjadi <em>hidden cost</em> bagi investor.
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_("Lihat Data: Sebaran 40 PN Nasional (Gabungan Semua Sumber)"), expanded=False):
        st.dataframe(_df_all_pn, use_container_width=True, hide_index=True)
        st.caption("📁 **Sumber File:** `data/final/sipp_all_pn_nasional.csv`")


# ══════════════════════════════════════════════════════════
# ═══════════ LAYER Y: DAMPAK EKONOMI ═════════════════════
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.markdown('<div style="background:#1B5E20;color:#C8E6C9;padding:8px 16px;border-radius:8px;font-size:1rem;font-weight:700;display:inline-block;">2. DAMPAK NYATA PADA IKLIM INVESTASI</div>', unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 1.4 GINI COEFFICIENT
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.1 Dampak: Bukti Investasi Hanya Berputar di Pusat"))

st.markdown('<span style="background:#B71C1C;color:#FFCDD2;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Gini Index Analisis (Variabel Y1)</span>', unsafe_allow_html=True)

gini_narrative = _("""Menggunakan metrik **Gini Coefficient** untuk mendeteksi seberapa merata triliunan modal disebar ke {n_prov} provinsi. Skala Gini bergerak dari 0 (Sangat Merata) hingga 1 (Ketimpangan Mutlak). Jika investasi mengalir sehat sesuai potensi wilayah, garis akan berada di zona hijau (< 0.4). Namun, akibat sentralisasi kepastian hukum, mayoritas investor memilih bermain aman dengan menumpuk modalnya di provinsi-provinsi pusat yang memiliki ekosistem hukum perlindungan investasi yang dominan—meninggalkan provinsi pinggiran minim kepastian.""")

gini_src = _("Dihitung menggunakan data agregat investasi per kuartal BKPM.")
st.markdown(gini_narrative.format(n_prov=n_prov_a) + f"\n\n<small><b>Sumber:</b> {gini_src}</small>", unsafe_allow_html=True)


gini_combined = pd.concat([gini_a, gini_d], ignore_index=True)
fig_gini = px.line(
    gini_combined, x="date", y="gini", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": "#FF3D00", "Investasi Domestik (PMDN)": "#B0BEC5"},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "gini": "Level Ketimpangan", "tipe": ""}
)
fig_gini.add_hrect(y0=0.4, y1=1, fillcolor="red", opacity=0.1, layer="below", line_width=0)
fig_gini.update_layout(
    height=400, yaxis=dict(range=[0, 1], gridcolor="#333"),
    title=dict(text="Ketimpangan Distribusi Modal (Indeks Gini)", font=dict(color="#E0E0E0", size=16)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20)
)
fig_gini.add_hline(y=0.4, line_dash="dash", line_color="#E53935")
fig_gini.add_annotation(
    x=gini_combined["date"].iloc[len(gini_combined)//2], y=0.55,
    text="ZONA KETIMPANGAN TINGGI (>0.4)",
    showarrow=False, font=dict(color="#E53935", size=18, weight="bold")
)
st.plotly_chart(fig_gini, use_container_width=True)

st.markdown(f'''
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #FF3D00; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi:</b> Ketimpangan distribusi investasi asing (PMA) terkonfirmasi di level <b>SANGAT TIMPANG (Gini = {latest_gini_a:.3f})</b>. Kondisi hukum dan birokrasi yang lebih prediktabel memicu terjadinya <i>agglomeration effect</i> di mana wilayah 'SADAR HUKUM' memonopoli arus modal massal.
</div>
''', unsafe_allow_html=True)

with st.expander(_("Lihat Data: Gini Coefficient per Kuartal"), expanded=False):
    st.dataframe(gini_combined.pivot_table(index="date", columns="tipe", values="gini").reset_index(), use_container_width=True, hide_index=True)
    st.caption("📁 **Sumber File:** Agregasi dari `data/final/realisasi_investasi_asing.csv` & `realisasi_investasi_domestik.csv`")


# ══════════════════════════════════════════════════
# 1.5 STD DEVIATION
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.2 Analisis Lanjut: Gejolak Modal Masuk (Standard Deviasi)"))
std_narrative = _("""Menggunakan metode **Standard Deviation** untuk mengukur volatilitas sebaran investasi.
SD PMA kuartal terakhir sebesar **{std_a:,.1f} IDR Bn** — artinya sebaran investasi antar provinsi sangat lebar.
SD PMDN di **{std_d:,.1f} IDR Bn** juga memperlihatkan volatilitas besar.""")

std_src = _("Agregasi <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code>")
st.markdown(std_narrative.format(std_a=latest_std_a, std_d=latest_std_d) +
            f"\n\n<small><b>Sumber:</b> {std_src}</small>", unsafe_allow_html=True)

std_combined = pd.concat([std_a, std_d], ignore_index=True)
fig_std = px.line(
    std_combined, x="date", y="std_dev", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": "#FF3D00", "Investasi Domestik (PMDN)": "#4CAF50"},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "std_dev": "Std. Deviation", "tipe": ""}
)
fig_std.update_layout(
    height=400,
    title=dict(text="Gejolak Ekstrem Sebaran Uang Masuk antar Kuartal", font=dict(color="#E0E0E0", size=16)),
    yaxis=dict(title="", gridcolor="#333"), xaxis=dict(title=""),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=60, b=20)
)
if not std_combined.empty:
    max_std = std_combined.loc[std_combined["std_dev"].idxmax()]
    fig_std.add_annotation(
        x=max_std["date"], y=max_std["std_dev"],
        text="Gejolak Ekstrem!<br>Konsentrasi menumpuk mendadak",
        showarrow=True, arrowhead=1, ax=-50, ay=30, font=dict(color="#FF3D00", size=14, weight="bold")
    )
st.plotly_chart(fig_std, use_container_width=True)

with st.expander(_("Lihat Data: Standard Deviation Volatilitas Investasi"), expanded=False):
    st.dataframe(std_combined.pivot_table(index="date", columns="tipe", values="std_dev").reset_index(), use_container_width=True, hide_index=True)
    st.caption("📁 **Sumber File:** Agregasi dari `data/final/realisasi_investasi_asing.csv` & `realisasi_investasi_domestik.csv`")


# ══════════════════════════════════════════════════
# 1.6 DISTRIBUSI PROVINSI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.3 Peta Ketimpangan: Siapa Dapat Uang, Siapa Tidak?"))

st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Extreme Ratio Analysis (Variabel Y3)</span>', unsafe_allow_html=True)

prov_narrative = _("""Sebagai proksi visual ketimpangan distribusi modal riil, analisis ini menarik komparatif gap rasio antara rata-rata dana investasi yang terserap provinsi "Pemenang" (Top 5) dibanding provinsi "Tertinggal" (Bottom 5). Secara teori ekonomi perwilayahan, gap natural wajar terjadi. Namun, perbedaan serapan modal yang pecah di level rasio esktrem merupakan sinyalemen kuat eksistensi **Threshold Kepastian Regulasi**. Mayoritas pemodal lebih merelakan uangnya bertarung profit di kawasan hiperkompetitif asalkan regulasinya jelas, dibandingkan mengambil diskon investasi di pasar wilayah tier-3 jika iklim kepastian hukumnya abu-abu.""")

st.markdown(prov_narrative + "\n\n<small><b>Sumber:</b> Agregasi rata-rata nilai kuartalan PMA/PMDN per provinsi.</small>", unsafe_allow_html=True)

# Hanya tampilkan ekstrim Top 5 dan Bottom 5 agar dramatis dan tidak kepanjangan
_df_prov = prov_avg.sort_values("rata_rata", ascending=True)
_df_prov_extreme = pd.concat([_df_prov.head(5), _df_prov.tail(5)])
colors_prov = ['#424242' if i < 5 else '#FF3D00' for i in range(10)]

fig_prov = go.Figure(go.Bar(
    x=_df_prov_extreme["rata_rata"], y=_df_prov_extreme["provinsi"], orientation="h",
    marker_color=colors_prov,
    text=_df_prov_extreme["rata_rata"].apply(lambda x: f"{x:,.0f} M"),
    textposition='outside', textfont_size=12
))
fig_prov.update_layout(
    height=450, margin=dict(l=20, r=80, t=50, b=20), showlegend=False,
    title=dict(text="Perbandingan Ekstrem: 5 Pemenang vs 5 Provinsi Tertinggal", font=dict(color="#E0E0E0", size=16)),
    xaxis=dict(title="", showgrid=False, showticklabels=False),
    yaxis=dict(title="", tickfont=dict(size=12, weight="bold"))
)
st.plotly_chart(fig_prov, use_container_width=True)

st.markdown(f'''
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi:</b> <strong>Rasio Kesenjangan Ekstrem:</strong> <b>{prov_top1['provinsi']}</b> di pulau utama dikucuri modal segar <span style="color:{C_WARN}; font-size:1.3rem; font-weight:800;">{ratio_top_bot:,.0f}x lipat</span> lebih bombastis dibanding provinsi terdalam <b>{prov_bot1['provinsi']}</b>. Monopoli 5 provinsi yang memborong <b>{top5_share:.1f}%</b> membuktikan bahwa <i>infrastruktur soft</i> (peradilan, kontrak/hukum bisnis daerah) memegang daya tawar setara infrastruktur beton.
</div>
''', unsafe_allow_html=True)

with st.expander(_("Lihat Data: Rata-rata Investasi per Provinsi"), expanded=False):
    st.dataframe(prov_avg.sort_values("rata_rata", ascending=False), use_container_width=True, hide_index=True)
    st.caption("📁 **Sumber File:** Agregasi rata-rata dari `data/final/realisasi_investasi_[asing/domestik].csv`")


# ══════════════════════════════════════════════════
# 1.7 ICOR NASIONAL
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.4 Biaya Siluman: Makin Mahal Biaya Investasi, Makin Sedikit Hasilnya"))

st.markdown('<span style="background:#F57F17;color:#FFF9C4;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Incremental Capital Output Ratio (Variabel Y4)</span>', unsafe_allow_html=True)

icor_narrative = _("""Indikator makro ekonomi **ICOR (Incremental Capital Output Ratio)** merekam tingkat efektivitas produktivitas alokasi modal sebuah negara. Mudahnya: berapa pundi-pundi investasi ekstra yang dibakar investor demi mencetak +1 digit output ekonomi. Titik efisien global untuk negara transisional dipatok di kisaran ~4.0. Skoring ICOR nasional yang melambung dari benchmark merepresentasikan kebocoran laten struktural akibat eksistensi pelik **Invisible Cost/Biaya Siluman**.  Pungutan pelicin perizinan tumpang-tindih, ongkos menyuap makelar penundaan peradilan (<i>delay damages</i>), serta tebusan premi risiko hukum masuk mengerek nafas operasional investor berlipat ganda dari kalkulasi fundamental.""")

st.markdown(icor_narrative + "\n\n<small><b>Sumber:</b> Data olahan rasio realisasi investasi terhadap penciptaan gross output.</small>", unsafe_allow_html=True)

fig_icor = go.Figure()
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pma"], mode="lines+markers", name="Ongkos Investasi Asing",
    line=dict(color="#FF9800", width=4), marker=dict(size=10)
))
fig_icor.add_hrect(y0=0, y1=4.0, fillcolor="green", opacity=0.1, layer="below", line_width=0)
fig_icor.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    title=dict(text="Lonjakan ICOR: Indikasi Kuat Kebocoran / Inefisiensi Hukum", font=dict(color="#E0E0E0", size=16)),
    yaxis=dict(title="", gridcolor="#333"), xaxis=dict(title=""),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(l=20, r=20, t=50, b=20)
)
fig_icor.add_hline(y=4.0, line_dash="dash", line_color="#4CAF50")
fig_icor.add_annotation(
    x=df_icor["date"].iloc[0], y=3.8,
    text="Batas Efisiensi Global (~4.0)",
    showarrow=False, font=dict(color="#4CAF50", size=12), xanchor="left"
)
min_icor = df_icor.loc[df_icor["icor_pma"].idxmin()]
if min_icor["icor_pma"] < 0:
    fig_icor.add_annotation(
        x=min_icor["date"], y=min_icor["icor_pma"],
        text="Anomali Numerik<br>(Dipicu Pertumbuhan Negatif)",
        showarrow=True, arrowhead=1, ax=45, ay=-30, font=dict(color="#E53935", size=14, weight="bold")
    )
st.plotly_chart(fig_icor, use_container_width=True)

st.markdown(f'''
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #FF9800; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi:</b> Menembusnya skor stagnan ICOR Nasional di tingkat <b>{icor_last:.2f}</b> menjadi saksi statistik paling telanjang bahwa beban kemudahan birokrasi permodalan sangat akut di Indonesia. Korporasi masa kini menelan kompensasi margin mahal dari <i>Risk Premium Inconsistency</i> hanya sekadar bertahan eksis operasional.
</div>
''', unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3. Kesimpulan: Hukum Tidak Pasti = Kesenjangan Ekstrem"))

st.markdown(f'''
<div style="background-color: #2F0A28; padding: 25px; border-radius: 10px; border: 1px solid #FF3D00;">
    <ul style="font-size: 1.1rem; line-height: 1.8; color: #E0E0E0; margin: 0; padding-left: 20px;">
        <li><b>Sengkarut Hukum itu Nyata:</b> <b>{_total_ma} putusan MA</b> bisnis dan puluhan izin investasi dicabut mendadak membuktikan ketidakpastian tinggi.</li>
        <li><b>Aturan Bisa Berbalik:</b> Reversal Rate <b>{_reversal_rate:.2f}%</b> berarti kemenangan bisnis di pengadilan bawah sangat rentan dibatalkan Mahkamah Agung.</li>
        <li><b>Daerah Ditinggalkan:</b> Investor lari ke zona aman hukum, membiarkan 10 provinsi terbawah hanya berebut kue sisa <b>{bot10_share:.1f}%</b>.</li>
        <li><b>Kesenjangan Ekstrem:</b> Gap ekonomi yang meraksasa ini bukan sekadar karena kurang jalan tol, tapi absennya jaminan rasa aman bagi bisnis (kepastian prosedur).</li>
        <li><b>Inefisiensi Membengkak:</b> Meroketnya ICOR membuktikan investor rela menelan ongkos lebih mahal demi "membeli" kepastian hukum daripada ekspansi.</li>
    </ul>
</div>
''', unsafe_allow_html=True)

st.markdown(f'''
<small style="color: #888; display: block; margin-top: 30px; text-align: center;">
    <em>Data dan narasi dihasilkan oleh kerangka LEUI (Legal Enforcement Uncertainty Index) CELIOS.</em>
</small>
''', unsafe_allow_html=True)
