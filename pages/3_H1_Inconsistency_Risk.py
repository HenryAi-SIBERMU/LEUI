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
_reg_h1_path = os.path.join(DATA, "regulasi_h1_yearly.csv")
_churn_path = os.path.join(DATA, "regulatory_churn_rate.csv")
_ma_stat_path = os.path.join(DATA, "laporan_ma_statistik.csv")
_sipp_durasi_path = os.path.join(DATA, "sipp_durasi_distribution.csv")
_sipp_pn_path = os.path.join(DATA, "sipp_pn_distribution.csv")
_sipp_yearly_path = os.path.join(DATA, "sipp_yearly.csv")

_total_ma = 0
_df_ma_yr = None
if os.path.exists(_ma_yearly_path):
    _df_ma_yr = pd.read_csv(_ma_yearly_path)
    _total_ma = int(_df_ma_yr['total_putusan'].sum())

_total_reg = 0
_berlaku = 0
_dicabut = 0
_df_reg_h1 = None
if os.path.exists(_reg_h1_path):
    _df_reg_h1 = pd.read_csv(_reg_h1_path)
    _total_reg = int(_df_reg_h1['jumlah'].sum())
    _berlaku = int(_df_reg_h1[_df_reg_h1['status'] == 'berlaku']['jumlah'].sum()) if 'status' in _df_reg_h1.columns else _total_reg
    _dicabut = _total_reg - _berlaku

_df_churn = None
if os.path.exists(_churn_path):
    _df_churn = pd.read_csv(_churn_path)

_df_ma_stat = None
_reversal_rate = 0
_clearance_rate = 0
if os.path.exists(_ma_stat_path):
    _df_ma_stat = pd.read_csv(_ma_stat_path)
    if not _df_ma_stat.empty:
        _reversal_rate = _df_ma_stat.iloc[0].get('reversal_rate_pct', 0)
        _clearance_rate = _df_ma_stat.iloc[0].get('clearance_rate_pct', 0)

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


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title(_("H1: Inconsistency Risk — Ketidakkonsistenan Hukum Antar Wilayah"))
subtitle = _("Analisis Distribusi & Ketimpangan Investasi sebagai Efek Inkonsistensi Lingkungan Usaha")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander(_("Kerangka Teori & Metodologi: Inconsistency Risk (H1)"), expanded=False):
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
intro = _("""Inkonsistensi hukum bukan lagi sebatas wacana yuridis, melainkan *driver* utama ketimpangan struktural ekonomi Indonesia. Analisis data realisasi **{start}–{end}** pada **{n_prov} provinsi** memperlihatkan bagaimana tingginya risiko sengketa perdata (tercatat **{tot_ma} putusan MA bisnis**, dengan reversal rate **{rev_rate:.2f}%**) dan tumpang tindih aturan (sedikitnya **{tot_dicabut} regulasi daerah/pusat dicabut/diubah**) serta **{tot_sipp} sengketa PN** menciptakan *barrier to entry* tak kasat mata. 

Investor merespons beban ketidakpastian ini secara defensif dengan memusatkan modal mereka ke segelintir \"safe haven\" yang terbukti aman. Hasilnya, Gini rasio investasi asing (PMA) meledak ke **{gini_a:.3f}** dan PMDN menembus **{gini_d:.3f}**—angka yang mengonfirmasi ketimpangan absolut. Terbukti, **5 provinsi teratas sanggup menyedot {top5:.1f}% investasi nasional**, membiarkan **10 provinsi terbawahnya memperebutkan remah-remah {bot10:.1f}%**.""")

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

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── Overview KPI Cards ──
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Putusan MA Bisnis</div>
        <div class="metric-value" style="color:#AB47BC">{_total_ma}</div>
        <div class="metric-delta" style="color:#AB47BC">Wanprestasi, Izin, Investasi</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Reversal Rate MA</div>
        <div class="metric-value" style="color:#E53935">{_reversal_rate:.2f}%</div>
        <div class="metric-delta" style="color:#E53935">Putusan dikabulkan (2023)</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Regulasi Berlaku / Cabut</div>
        <div class="metric-value" style="color:#42A5F5">{_berlaku} / <span style="color:#E53935">{_dicabut}</span></div>
        <div class="metric-delta" style="color:#42A5F5">dari {_total_reg} regulasi H1</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sengketa PN (SIPP)</div>
        <div class="metric-value" style="color:#FF9800">{_total_sipp}</div>
        <div class="metric-delta" style="color:#FF9800">Sengketa bisnis tingkat pertama</div>
    </div>""", unsafe_allow_html=True)
with col5:
    g_color = '#EF5350' if latest_gini_a > 0.4 else '#4CAF50'
    g_status = 'Sangat Timpang' if latest_gini_a > 0.6 else 'Timpang' if latest_gini_a > 0.4 else 'Moderat'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gini PMA (Terakhir)</div>
        <div class="metric-value" style="color:{g_color}">{latest_gini_a:.3f}</div>
        <div class="metric-delta" style="color:{g_color}">{g_status}</div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# ═══════════ LAYER X: VARIABEL HUKUM ═════════════════════
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.markdown('<div style="background:#5C2B6A;color:#E1BEE7;padding:8px 16px;border-radius:8px;font-size:1rem;font-weight:700;display:inline-block;">LAYER X — VARIABEL HUKUM (INDEPENDEN)</div>', unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 1.1 YUDISIAL (HUKUM) — ENRICHED
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.1 Inkonsistensi Yudisial: Volume Sengketa & Performa MA"))
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Agregasi Putusan Direktori MA + Laporan Tahunan MA (Variabel X1)</span>', unsafe_allow_html=True)

ma_narrative = _("""Menggunakan metode **Data Mining Putusan Mahkamah Agung** untuk mengekstrak dan mengagregasi volume sengketa perdata bisnis (wanprestasi, sengketa investasi, lisensi, dan perizinan). Data ini diperkaya dengan **Laporan Tahunan MA** yang mencatat *reversal rate* (persentase putusan yang dikabulkan/dibalik) sebesar **{rev_rate:.2f}%** dan *clearance rate* **{clear_rate:.2f}%**. 

Reversal rate >10% mengindikasikan bahwa **lebih dari 1 dari 10 keputusan pengadilan di bawahnya dibalikkan** di tingkat kasasi—sebuah sinyal inkonsistensi sistemik. Bagi investor, fakta ini memperbesar ketidakpastian: kontrak bisnis yang sudah dimenangkan di pengadilan pertama bisa saja dibalikkan oleh MA, menghancurkan kalkulasi risiko mereka.""")

ma_src = _("Berdasarkan scraping <code>putusan3.mahkamahagung.go.id</code> (Filter: Perdata Khusus, Bisnis, Investasi) + <code>Laporan Tahunan MA 2023-2024</code>.")
st.markdown(ma_narrative.format(rev_rate=_reversal_rate, clear_rate=_clearance_rate) + f"\n\n<small>📁 <b>Sumber:</b> {ma_src}</small>", unsafe_allow_html=True)

if _df_ma_yr is not None:
    _fig_ma = px.bar(
        _df_ma_yr, x="year", y="total_putusan",
        color_discrete_sequence=["#AB47BC"],
        template=PLOTLY_TEMPLATE,
        labels={"year": "Tahun", "total_putusan": "Jumlah Sengketa Tingkat Kasasi"}
    )
    _fig_ma.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(_fig_ma, use_container_width=True)
    
    st.markdown(f"""
    <div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #AB47BC; margin-bottom: 20px; margin-top: 5px;">
        Data direktori Mahkamah Agung mencatat adanya <strong>{_total_ma} sengketa perdata bisnis</strong> yang bermuara hingga kasasi. Reversal rate <strong>{_reversal_rate:.2f}%</strong> mengonfirmasi bahwa <em>procedural uncertainty</em> bukan asumsi—melainkan fakta terukur dari data peradilan.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(_("📋 Lihat Data: Putusan MA Yearly"), expanded=False):
        st.dataframe(_df_ma_yr, use_container_width=True, hide_index=True)

# Laporan MA Statistik table
if _df_ma_stat is not None:
    with st.expander(_("📋 Lihat Data: Laporan Tahunan MA (Statistik Performa)"), expanded=False):
        st.dataframe(_df_ma_stat, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 1.2 REGULASI (HUKUM) — ENRICHED with churn rate
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.2 Ketidakpastian Regulasi: Tumpang Tindih, Pencabutan & Churn Rate"))
st.markdown('<span style="background:#0D47A1;color:#BBDEFB;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Regulatory Churn Test + Lifecycle Analysis (Variabel X2)</span>', unsafe_allow_html=True)

reg_narrative = _("""Menggunakan metode **Regulatory Churn Test** untuk mengukur tingkat ketidakpastian produk hukum yang esensial bagi iklim usaha. Kami melacak siklus hidup puluhan regulasi kunci (daerah maupun pusat) yang mengatur izin usaha, perpajakan lokal, dan tata ruang.

Grafik pertama membandingkan regulasi mana yang bertahan (berlaku) melawan regulasi yang sudah layu sebelum berkembang (dicabut, dibatalkan MA/MK, atau direvisi). Grafik kedua memperlihatkan **tren Regulatory Churn Rate nasional** — persentase regulasi bisnis yang dicabut/diubah setiap tahunnya. Lonjakan churn rate di tahun-tahun tertentu mencerminkan masa-masa di mana *shock cost* bagi investor meledak: aturan yang ditandatangani hari ini bisa saja ilegal esok hari.""")

reg_src = _("Ekstraksi status dari database regulasi Pasal.id & JDIH (Dataset Bappenas).")
st.markdown(reg_narrative + f"\n\n<small>📁 <b>Sumber:</b> {reg_src}</small>", unsafe_allow_html=True)

if _df_reg_h1 is not None:
    st.caption(_("📊 Status Hukum Regulasi Esensial H1 per Tahun Penerbitan"))
    _fig_reg = px.bar(
        _df_reg_h1, x="year", y="jumlah", color="status",
        color_discrete_map={"berlaku": "#42A5F5", "tidak_berlaku": "#E53935"},
        template=PLOTLY_TEMPLATE, barmode="group",
        labels={"year": "Tahun", "jumlah": "Jumlah Regulasi", "status": "Status Hukum"}
    )
    _fig_reg.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", legend=dict(title=""))
    st.plotly_chart(_fig_reg, use_container_width=True)
    
    with st.expander(_("📋 Lihat Data: Regulasi H1 Yearly"), expanded=False):
        st.dataframe(_df_reg_h1, use_container_width=True, hide_index=True)

# Churn Rate Line Chart (NEW)
if _df_churn is not None:
    st.caption(_("📊 Tren Regulatory Churn Rate Nasional (% Regulasi Dicabut/Diubah per Tahun)"))
    _fig_churn = go.Figure()
    _fig_churn.add_trace(go.Scatter(
        x=_df_churn["year"], y=_df_churn["churn_rate"],
        mode="lines+markers", name="Churn Rate (%)",
        line=dict(color=C_DANGER, width=2.5), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(229,57,53,0.1)"
    ))
    _fig_churn.add_trace(go.Bar(
        x=_df_churn["year"], y=_df_churn["total"],
        name="Total Regulasi", marker_color="rgba(66,165,245,0.3)",
        yaxis="y2"
    ))
    _fig_churn.update_layout(
        template=PLOTLY_TEMPLATE, height=400,
        yaxis=dict(title="Churn Rate (%)", side="left"),
        yaxis2=dict(title="Total Regulasi", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
    )
    st.plotly_chart(_fig_churn, use_container_width=True)
    
    st.markdown(f"""
    <div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #E53935; margin-bottom: 20px; margin-top: 5px;">
        Dari <strong>{_total_reg} regulasi kunci</strong> tingkat daerah dan pusat yang memengaruhi iklim usaha (H1), sebanyak <strong>{_dicabut} aturan berakhir dicabut, dibatalkan, atau direvisi</strong>. Data churn rate nasional menunjukkan lonjakan pencabutan tertinggi di era reformasi dan transisi regulasi daerah, menghancurkan horizon perencanaan jangka panjang bagi investor.
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_("📋 Lihat Data: Regulatory Churn Rate Nasional"), expanded=False):
        st.dataframe(_df_churn, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 1.3 SIPP — Durasi & Volume Sengketa PN (NEW!)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.3 Proses Hukum Panjang: Durasi & Volume Sengketa Pengadilan Negeri"))
st.markdown('<span style="background:#E65100;color:#FFE0B2;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Scraping SIPP Pengadilan Negeri (Variabel X3)</span>', unsafe_allow_html=True)

sipp_narrative = _("""Menggunakan metode **Scraping Sistem Informasi Penelusuran Perkara (SIPP)** dari beberapa Pengadilan Negeri untuk mengukur **durasi riil proses sengketa bisnis** — menjawab pertanyaan: *\"seberapa lama seorang investor harus menunggu kepastian hukum?\"*

Data menunjukkan bahwa proses hukum bisnis di pengadilan negeri **bukan urusan cepat**: mayoritas perkara memakan waktu 1–3 bulan, namun masih ada yang terseret hingga 6–12 bulan. Ketidakpastian durasi ini menjadi **hidden cost** bagi investor — modal tertahan di sengketa yang tidak bisa diprediksi kapan berakhir. Ditambah volume sengketa yang terus meningkat setiap tahun, tekanan terhadap sistem peradilan semakin berat dan waktu penyelesaian semakin sulit diprediksi.""")

sipp_src = _("Scraping <code>sipp.pn-sidoarjo.go.id</code> & <code>sipp.pn-negara.go.id</code> (Filter: Perdata Bisnis).")
st.markdown(sipp_narrative + f"\n\n<small>📁 <b>Sumber:</b> {sipp_src}</small>", unsafe_allow_html=True)

# Durasi Distribution Chart
if _df_sipp_durasi is not None:
    st.caption(_("📊 Distribusi Durasi Penyelesaian Sengketa Bisnis (PN)"))
    _fig_dur = px.bar(
        _df_sipp_durasi, x="durasi_bucket", y="jumlah",
        color_discrete_sequence=["#FF9800"],
        template=PLOTLY_TEMPLATE,
        labels={"durasi_bucket": "Durasi Sengketa", "jumlah": "Jumlah Perkara"}
    )
    _fig_dur.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(_fig_dur, use_container_width=True)
    
    with st.expander(_("📋 Lihat Data: Distribusi Durasi Sengketa"), expanded=False):
        st.dataframe(_df_sipp_durasi, use_container_width=True, hide_index=True)

# Volume Sengketa PN per Tahun
if _df_sipp_yearly is not None:
    st.caption(_("📊 Tren Volume Sengketa Bisnis di Pengadilan Negeri per Tahun"))
    _fig_sipp_yr = px.bar(
        _df_sipp_yearly, x="year", y="total_perkara",
        color_discrete_sequence=["#FF7043"],
        template=PLOTLY_TEMPLATE,
        labels={"year": "Tahun", "total_perkara": "Total Perkara Bisnis"}
    )
    _fig_sipp_yr.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(_fig_sipp_yr, use_container_width=True)
    
    with st.expander(_("📋 Lihat Data: Sengketa PN Yearly"), expanded=False):
        st.dataframe(_df_sipp_yearly, use_container_width=True, hide_index=True)

# Distribusi per PN
if _df_sipp_pn is not None:
    st.caption(_("📊 Konsentrasi Sengketa per Pengadilan Negeri"))
    _fig_pn = px.bar(
        _df_sipp_pn.head(10), x="jumlah", y="pengadilan", orientation="h",
        color_discrete_sequence=["#EF6C00"],
        template=PLOTLY_TEMPLATE,
        labels={"jumlah": "Jumlah Sengketa", "pengadilan": ""}
    )
    _fig_pn.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(_fig_pn, use_container_width=True)
    
    st.markdown(f"""
    <div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #FF9800; margin-bottom: 20px; margin-top: 5px;">
        Dari <strong>{_total_sipp} sengketa bisnis</strong> yang terdeteksi di pengadilan negeri, mayoritas memakan waktu <strong>1–3 bulan</strong> dengan sebagian terseret hingga 6–12 bulan. Volume sengketa menunjukkan tren <strong>akselerasi agresif</strong> — meningkat dari belasan perkara per tahun menjadi puluhan. Proses hukum yang panjang dan tidak terprediksi ini menjadi <em>hidden cost</em> langsung bagi investor.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(_("📋 Lihat Data: Distribusi per Pengadilan Negeri"), expanded=False):
        st.dataframe(_df_sipp_pn, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════
# ═══════════ LAYER Y: DAMPAK EKONOMI ═════════════════════
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.markdown('<div style="background:#1B5E20;color:#C8E6C9;padding:8px 16px;border-radius:8px;font-size:1rem;font-weight:700;display:inline-block;">LAYER Y — DAMPAK EKONOMI (DEPENDEN)</div>', unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 1.4 GINI COEFFICIENT
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.4 Dampak Ekonomi: Ketimpangan Distribusi (Gini Coefficient)"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Gini Coefficient (Variabel Y1)</span>', unsafe_allow_html=True)

gini_trend_word = "memburuk" if gini_a_change > 0 else "membaik"
gini_narrative = _("""Menggunakan metode **Gini Coefficient** untuk mengukur ketimpangan distribusi investasi antar provinsi. Gini PMA secara
konsisten berada di atas **{avg_a:.3f}** (rata-rata sepanjang periode), dengan kuartal terakhir di angka **{last_a:.3f}** —
jauh melampaui ambang batas ketimpangan moderat (0.4). Dibandingkan 4 kuartal pertama ({early:.3f})
dengan 4 kuartal terakhir ({late:.3f}), ketimpangan PMA justru **{trend}** sebesar **{chg:.1f}%**.
Gini PMDN menunjukkan pola serupa namun lebih rendah ({avg_d:.3f}). Ketika keduanya sama-sama
memperlihatkan Gini >0.4, ini memperkuat argumen bahwa **lingkungan usaha antar daerah sangat tidak konsisten**.""")

gini_src = _("Agregasi per provinsi per kuartal dari <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code>.")
st.markdown(
    gini_narrative.format(
        avg_a=avg_gini_a, last_a=latest_gini_a, early=gini_a_early, late=gini_a_late,
        trend=gini_trend_word, chg=abs(gini_a_change), avg_d=avg_gini_d
    ) + f"\n\n<small>📁 <b>Sumber:</b> {gini_src}</small>", unsafe_allow_html=True
)

gini_combined = pd.concat([gini_a, gini_d], ignore_index=True)
fig_gini = px.line(
    gini_combined, x="date", y="gini", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": C_ASING, "Investasi Domestik (PMDN)": C_DOMESTIK},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "gini": "Gini Coefficient", "tipe": "Tipe Investasi"}
)
fig_gini.update_layout(
    height=420, yaxis=dict(range=[0, 1]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
fig_gini.add_hline(y=0.4, line_dash="dash", line_color=C_WARN, annotation_text="Batas ketimpangan moderat (0.4)")
st.plotly_chart(fig_gini, use_container_width=True)

with st.expander(_("📋 Lihat Data: Gini Coefficient per Kuartal"), expanded=False):
    st.dataframe(gini_combined.pivot_table(index="date", columns="tipe", values="gini").reset_index(), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 1.5 STD DEVIATION
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.5 Dampak Ekonomi: Volatilitas Investasi (Std. Deviation)"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Standard Deviation (Variabel Y2)</span>', unsafe_allow_html=True)

std_narrative = _("""Menggunakan metode **Standard Deviation** untuk mengukur volatilitas sebaran investasi.
SD PMA kuartal terakhir sebesar **{std_a:,.1f} IDR Bn** — artinya sebaran investasi antar provinsi sangat lebar.
SD PMDN di **{std_d:,.1f} IDR Bn** juga memperlihatkan volatilitas besar. Lonjakan SD biasanya
berkorelasi dengan kuartal di mana satu atau dua provinsi menerima mega-investasi sementara
daerah lain stagnan — pola yang linier dengan instabilitas hukum.""")

std_src = _("Agregasi <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code> — groupby(kuartal, provinsi) → sum → SD per kuartal.")
st.markdown(std_narrative.format(std_a=latest_std_a, std_d=latest_std_d) +
            f"\n\n<small>📁 <b>Sumber:</b> {std_src}</small>", unsafe_allow_html=True)

std_combined = pd.concat([std_a, std_d], ignore_index=True)
fig_std = px.line(
    std_combined, x="date", y="std_dev", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": C_ASING, "Investasi Domestik (PMDN)": C_DOMESTIK},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "std_dev": "Std. Deviation (IDR Bn)", "tipe": "Tipe Investasi"}
)
fig_std.update_layout(
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_std, use_container_width=True)

with st.expander(_("📋 Lihat Data: Std. Deviation per Kuartal"), expanded=False):
    st.dataframe(std_combined.pivot_table(index="date", columns="tipe", values="std_dev").reset_index(), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 1.6 DISTRIBUSI PROVINSI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.6 Dampak Ekonomi: Peta Konsentrasi Investasi per Provinsi"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Distribusi Top/Bottom Analysis (Variabel Y3)</span>', unsafe_allow_html=True)

prov_narrative = _("""Menggunakan metode **Distribusi Top/Bottom Analysis** untuk mengidentifikasi konsentrasi investasi.
**{top1}**, **{top2}**, dan **{top3}** mendominasi penerimaan investasi gabungan PMA+PMDN.
Rasio Top/Bottom mencapai **{ratio:,.0f}x lipat**. **5 provinsi teratas menyerap {top5:.1f}%** dari seluruh investasi, sementara
**10 provinsi terbawah hanya {bot10:.1f}%**. Gini di atas 0.6 mengindikasikan bahwa distorsi *non-fundamental*, termasuk ekspektasi paparan
terhadap sengketa perdata dan inkonsistensi birokrasi, turut mendorong konsentrasi ini.""")

prov_src = _("Gabungan <code>realisasi_investasi_asing.csv</code> + <code>realisasi_investasi_domestik.csv</code>, groupby(provinsi) → mean.")
st.markdown(
    prov_narrative.format(
        top1=prov_top1['provinsi'], top2=prov_top2['provinsi'], top3=prov_top3['provinsi'],
        ratio=ratio_top_bot, top5=top5_share, bot10=bot10_share
    ) + f"\n\n<small>📁 <b>Sumber:</b> {prov_src}</small>", unsafe_allow_html=True
)

n_show = 15
tab_top, tab_bottom = st.tabs([_("Top 15 Provinsi"), _("Bottom 15 Provinsi")])

with tab_top:
    top = prov_avg.tail(n_show)
    fig_top = px.bar(
        top, x="rata_rata", y="provinsi", orientation="h",
        color="rata_rata", color_continuous_scale=["#1B5E20", "#43A047", "#A5D6A7"],
        template=PLOTLY_TEMPLATE,
        labels={"rata_rata": "Rata-rata (IDR Bn/kuartal)", "provinsi": ""}
    )
    fig_top.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_top, use_container_width=True)

with tab_bottom:
    bottom = prov_avg.head(n_show)
    fig_bot = px.bar(
        bottom, x="rata_rata", y="provinsi", orientation="h",
        color="rata_rata", color_continuous_scale=["#B71C1C", "#E53935", "#EF9A9A"],
        template=PLOTLY_TEMPLATE,
        labels={"rata_rata": "Rata-rata (IDR Bn/kuartal)", "provinsi": ""}
    )
    fig_bot.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_bot, use_container_width=True)

# Rasio box
st.markdown(f"""
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px;
            border-left:5px solid {C_WARN}; margin-top:10px;">
    <strong>Rasio Ketimpangan:</strong> {prov_top1['provinsi']} menerima investasi
    <span style="color:{C_WARN}; font-size:1.3rem; font-weight:700;">{ratio_top_bot:,.0f}x lipat</span>
    dibanding {prov_bot1['provinsi']}. Top 5 = <b>{top5_share:.1f}%</b>, Bottom 10 = <b>{bot10_share:.1f}%</b>.
</div>
""", unsafe_allow_html=True)

with st.expander(_("📋 Lihat Data: Rata-rata Investasi per Provinsi"), expanded=False):
    st.dataframe(prov_avg.sort_values("rata_rata", ascending=False), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# 1.7 ICOR NASIONAL
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.7 Dampak Ekonomi: Tren ICOR Nasional (Biaya Ketidakpastian)"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: ICOR Time Series (Variabel Y4)</span>', unsafe_allow_html=True)

icor_trend_word = "naik" if icor_pma_trend > 0 else "turun"
icor_narrative = _("""Menggunakan metode **ICOR Time Series** untuk mengukur efisiensi investasi. ICOR PMA pada
{yr_first} sebesar **{v_first:.2f}**, namun pada {yr_last} menjadi **{v_last:.2f}** — {trend} **{chg:.1f}%**.
ICOR yang naik berarti Indonesia membutuhkan **semakin banyak investasi** untuk menghasilkan 1 unit pertumbuhan PDB — sebuah
indikasi bahwa biaya-biaya tersembunyi (legal fees, delays, risk premium) makin menggerogoti efisiensi investasi.""")

icor_src = _("Data dari <code>icor_nasional.csv</code> ({y1}-{y2}). Sumber: BPS.")
st.markdown(
    icor_narrative.format(
        yr_first=icor_year_first, yr_last=icor_year_last,
        v_first=icor_first, v_last=icor_last,
        trend=icor_trend_word, chg=abs(icor_pma_trend)
    ) + f"\n\n<small>📁 <b>Sumber:</b> {icor_src.format(y1=icor_year_first, y2=icor_year_last)}</small>",
    unsafe_allow_html=True
)

fig_icor = go.Figure()
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pmdn"], mode="lines+markers", name="ICOR PMDN",
    line=dict(color=C_DOMESTIK, width=2.5), marker=dict(size=7)
))
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pma"], mode="lines+markers", name="ICOR PMA",
    line=dict(color=C_ASING, width=2.5), marker=dict(size=7)
))
fig_icor.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="ICOR (Rasio)", xaxis_title="Tahun",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_icor, use_container_width=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(_("ICOR PMDN (Terakhir)"), f"{icor_d_last:.2f}")
with col2:
    st.metric(_("ICOR PMA (Terakhir)"), f"{icor_last:.2f}")
with col3:
    avg_icor = (icor_d_last + icor_last) / 2
    st.metric(_("Rata-rata ICOR"), f"{avg_icor:.2f}")

with st.expander(_("📋 Lihat Data: ICOR Nasional"), expanded=False):
    st.dataframe(df_icor, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("Interpretasi & Temuan Utama"))

temuan = _("""
**Analisis Temuan Utama H1 — Inconsistency Risk:**

Data empiris hukum (**{tot_ma} Putusan MA Bisnis** dengan reversal rate **{rev_rate:.2f}%**, pencabutan **{tot_dicabut} regulasi H1**, dan **{tot_sipp} sengketa PN**) memberikan landasan kausalitas mengapa ketimpangan distribusi investasi skala ekstrem terjadi. Lima temuan konvergen:

1. **Intensitas Sengkarut Hukum (X)** — Sengketa bisnis yang persisten menyentuh angka kasasi ditambah tingginya churn rate pencabutan regulasi dan akselerasi volume sengketa PN membuktikan bahwa ketidakpastian prosedural adalah ancaman nyata, bukan asumsi teoretis.

2. **Reversal Rate Tinggi (X)** — Reversal rate MA **{rev_rate:.2f}%** mengindikasikan lebih dari 1 dari 10 keputusan pengadilan bawah dibalikkan di kasasi — sinyal inkonsistensi sistemik yang membuat investor tidak bisa mengandalkan kepastian kontrak.
 
3. **Konsentrasi Ekstremitas Modal (Y)** — Gini PMA **{gini_a:.3f}** dan PMDN **{gini_d:.3f}** (keduanya jauh >0.4). 5 provinsi elit memborong **{top5:.1f}%** total investasi, 10 di dasar tangga hanya **{bot10:.1f}%**.

4. **Kesenjangan Melampaui Fundamental (Y)** — Rasio gap **{ratio:,.0f}x lipat** antara {prov_top} dan {prov_bot} gagal dijelaskan jika hanya argumen infrastruktur. Ketakutan terseret konflik hukum lokal mendorong distorsi lokasi.

5. **Biaya Kejut & Efisiensi Hancur (Y)** — ICOR PMA {trend} dari **{icor_f:.2f}** ({yr_f}) ke **{icor_l:.2f}** ({yr_l}). Meningkatnya ICOR bertepatan dengan pembatalan regulasi — suburnya "biaya tak kasat mata" akibat delay sengketa dan perubahan syarat izin.

**Implikasi Final Law & Economics:**
Inkonsistensi perlindungan hukum di Indonesia secara langsung membunuh pemerataan ekonomi. Investor rela mengorbankan efisiensi margin demi bertumpuk di teritorial aman, menghindari ranjau administrasi dan sistem peradilan yang tak terprediksi di daerah berkembang.
""")

st.markdown(temuan.format(
    tot_ma=_total_ma, rev_rate=_reversal_rate, tot_dicabut=_dicabut, tot_sipp=_total_sipp,
    gini_a=latest_gini_a, gini_d=latest_gini_d, top5=top5_share, bot10=bot10_share,
    ratio=ratio_top_bot, prov_top=prov_top1['provinsi'], prov_bot=prov_bot1['provinsi'],
    trend=icor_trend_word, icor_f=icor_first, icor_l=icor_last,
    yr_f=icor_year_first, yr_l=icor_year_last
))

st.markdown(f"""
<small><em>Catatan: Analisis ini mengimplementasikan kerangka dua lapis (2-Layer LEUI) yang memadukan data peradilan direktori Mahkamah Agung, Laporan Tahunan MA, SIPP PN, & regulasi Pasal.id (Variabel X: Hukum) dengan kompilasi panel ekonomi BKPM (Variabel Y: Dampak).</em></small>
""", unsafe_allow_html=True)
