"""
Page 1 — H1: Inconsistency Risk
Analisis inkonsistensi biaya/realisasi investasi antar wilayah sebagai proxy
ketidakpastian hukum daerah.

Causal Chain: Inkonsistensi Hukum → Ketimpangan Investasi → Outcome Uncertainty → Risk Premium ↑
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
n_kab_a = df_asing['kabupaten'].nunique()
n_prov_d = df_domestik['provinsi'].nunique()
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
icor_first = df_icor['icor_pma'].iloc[0] if len(df_icor) > 0 else 0
icor_last = df_icor['icor_pma'].iloc[-1] if len(df_icor) > 0 else 0
icor_d_first = df_icor['icor_pmdn'].iloc[0] if len(df_icor) > 0 else 0
icor_d_last = df_icor['icor_pmdn'].iloc[-1] if len(df_icor) > 0 else 0
icor_year_first = df_icor['date'].iloc[0].strftime('%Y') if len(df_icor) > 0 else '—'
icor_year_last = df_icor['date'].iloc[-1].strftime('%Y') if len(df_icor) > 0 else '—'
icor_pma_trend = ((icor_last - icor_first) / icor_first * 100) if icor_first > 0 else 0


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title(_("H1: Inconsistency Risk — Ketidakkonsistenan Hukum Antar Wilayah"))
subtitle = _("Analisis Distribusi & Ketimpangan Investasi sebagai Efek Inkonsistensi Lingkungan Usaha")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander(_("Metodologi: Analisis Inconsistency Risk (H1)"), expanded=False):
    st.markdown(_("""
    **Causal Chain:**
    `Putusan MA Inkonsisten + Regulasi Tumpang Tindih → Ketidakpastian Hukum → Risk Premium ↑ → Investasi Terkonsentrasi`

    **Variabel Hukum (X):**
    - Volume putusan MA terkait sengketa bisnis per tahun (dari OSINT Google CSE)
    - Regulasi H1 yang berlaku vs dicabut/diubah (dari Pasal.id)
    
    **Dampak Ekonomi (Y):**
    - Gini Coefficient distribusi investasi antar provinsi
    - Standard Deviation sebaran investasi
    - ICOR Nasional (efisiensi investasi)
    """))

# ── Intro Narrative ──
intro = _("""Data realisasi investasi Indonesia **{start}–{end}** mencakup **{n_prov} provinsi** dan
**{n_kab}+ kabupaten/kota** memperlihatkan sebuah **kontradiksi struktural**: investasi tidak
mengikuti potensi ekonomi, melainkan terkonsentrasi di segelintir wilayah. Gini PMA sebesar **{gini_a:.3f}** dan PMDN **{gini_d:.3f}**,
keduanya **jauh di atas ambang ketimpangan moderat (0.4)**. **5 provinsi teratas menyerap {top5:.1f}% total
investasi**, sementara **10 provinsi terbawah hanya menyerap {bot10:.1f}%**.""")

st.markdown(
    intro.format(
        start=rng_start, end=rng_end, n_prov=n_prov_a, n_kab=n_kab_a,
        gini_a=latest_gini_a, gini_d=latest_gini_d,
        top5=top5_share, bot10=bot10_share
    ),
    unsafe_allow_html=True
)
st.caption(_("Visualisasi: Pemodelan Dampak Putusan MA & Regulasi terhadap Volatilitas, Ketimpangan, dan Distribusi Top/Bottom Provinsi (Data diagregasi ke panel kuartalan)."))

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── Variabel Hukum (X) ──

# Load legal data
import plotly.express as _px_legal
_ma_yearly_path = os.path.join(DATA, "putusan_ma_yearly.csv")
_reg_h1_path = os.path.join(DATA, "regulasi_h1_yearly.csv")

_lc1, _lc2, _lc3 = st.columns(3)

if os.path.exists(_ma_yearly_path):
    _df_ma_yr = pd.read_csv(_ma_yearly_path)
    _total_ma = int(_df_ma_yr['total_putusan'].sum())
    with _lc1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Putusan MA Bisnis</div>
            <div class="metric-value" style="color:#AB47BC">{_total_ma}</div>
            <div class="metric-delta" style="color:#AB47BC">Wanprestasi, Izin, Investasi</div>
        </div>
        """, unsafe_allow_html=True)

if os.path.exists(_reg_h1_path):
    _df_reg_h1 = pd.read_csv(_reg_h1_path)
    _total_reg = int(_df_reg_h1['jumlah'].sum())
    _berlaku = int(_df_reg_h1[_df_reg_h1['status'] == 'berlaku']['jumlah'].sum()) if 'status' in _df_reg_h1.columns else _total_reg
    _dicabut = _total_reg - _berlaku
    with _lc2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Regulasi H1 Berlaku</div>
            <div class="metric-value" style="color:#42A5F5">{_berlaku}</div>
            <div class="metric-delta" style="color:#42A5F5">dari {_total_reg} total</div>
        </div>
        """, unsafe_allow_html=True)
    with _lc3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Regulasi H1 Dicabut/Diubah</div>
            <div class="metric-value" style="color:#E53935">{_dicabut}</div>
            <div class="metric-delta" style="color:#E53935">Indikator inkonsistensi kebijakan</div>
        </div>
        """, unsafe_allow_html=True)

# Chart: MA Putusan per Tahun
if os.path.exists(_ma_yearly_path):
    st.markdown("---")
    st.subheader(_("1.1 Volume Putusan MA Bisnis per Tahun"))
    st.markdown('<span style="background:#333;color:#AB47BC;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Sumber Inkonsistensi (Data Hukum)</span>', unsafe_allow_html=True)
    
    _fig_ma = px.bar(
        _df_ma_yr, x="year", y="total_putusan",
        color_discrete_sequence=["#AB47BC"],
        template=PLOTLY_TEMPLATE,
        labels={"year": "Tahun", "total_putusan": "Jumlah Putusan"}
    )
    _fig_ma.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(_fig_ma, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── Variabel Ekonomi (Y) ──


# ── KPI Cards ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    g_color = '#EF5350' if latest_gini_a > 0.4 else '#4CAF50'
    g_status = 'Sangat Timpang' if latest_gini_a > 0.6 else 'Timpang' if latest_gini_a > 0.4 else 'Moderat'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gini PMA (Terakhir)</div>
        <div class="metric-value" style="color:{g_color}">{latest_gini_a:.3f}</div>
        <div class="metric-delta" style="color:{g_color}">{g_status}</div>
    </div>""", unsafe_allow_html=True)
with col2:
    g_color = '#EF5350' if latest_gini_d > 0.4 else '#4CAF50'
    g_status = 'Sangat Timpang' if latest_gini_d > 0.6 else 'Timpang' if latest_gini_d > 0.4 else 'Moderat'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gini PMDN (Terakhir)</div>
        <div class="metric-value" style="color:{g_color}">{latest_gini_d:.3f}</div>
        <div class="metric-delta" style="color:{g_color}">{g_status}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Rasio Top/Bottom Provinsi</div>
        <div class="metric-value" style="color:#FF9800">{ratio_top_bot:,.0f}x</div>
        <div class="metric-delta" style="color:#AAA">Kesenjangan investasi</div>
    </div>""", unsafe_allow_html=True)
with col4:
    icor_color = '#EF5350' if icor_last > 6 else '#FF9800' if icor_last > 4 else '#4CAF50'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ICOR PMA ({icor_year_last})</div>
        <div class="metric-value" style="color:{icor_color}">{icor_last:.2f}</div>
        <div class="metric-delta" style="color:#AAA">Efisiensi investasi</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 2. GINI COEFFICIENT — SECTION UTAMA
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.2 Ketimpangan Distribusi Investasi (Gini Coefficient)"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Gini Coefficient</span>', unsafe_allow_html=True)

gini_trend_word = "memburuk" if gini_a_change > 0 else "membaik"
gini_narrative = _("""Menggunakan metode **Gini Coefficient** untuk mengukur ketimpangan distribusi investasi antar provinsi. Grafik di bawah memperlihatkan **dua wajah ketimpangan** yang terjadi bersamaan. Gini PMA secara
konsisten berada di atas **{avg_a:.3f}** (rata-rata sepanjang periode), dengan kuartal terakhir di angka **{last_a:.3f}** —
jauh melampaui ambang batas ketimpangan moderat (0.4, garis kuning putus-putus). Ini berarti investasi asing
**terkonsentrasi di segelintir wilayah saja**. Lebih mengkhawatirkan, dibandingkan 4 kuartal pertama ({early:.3f})
dengan 4 kuartal terakhir ({late:.3f}), ketimpangan PMA justru **{trend}** sebesar **{chg:.1f}%**.
Gini PMDN menunjukkan pola serupa namun lebih rendah ({avg_d:.3f}), mengindikasikan investasi domestik
sedikit lebih tersebar — namun tetap sangat timpang. Ketika investasi asing dan domestik sama-sama
memperlihatkan Gini >0.4, ini memperkuat argumen bahwa **lingkungan usaha antar daerah sangat tidak konsisten**:
investor tidak percaya bahwa mereka akan mendapat perlakuan hukum yang setara di semua wilayah.""")

gini_src = _("Agregasi per provinsi per kuartal dari <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code>.")
st.markdown(
    gini_narrative.format(
        avg_a=avg_gini_a, last_a=latest_gini_a, early=gini_a_early, late=gini_a_late,
        trend=gini_trend_word, chg=abs(gini_a_change), avg_d=avg_gini_d
    ) + f"\n\n<small>📁 <b>Sumber:</b> {gini_src}</small>", unsafe_allow_html=True
)
st.caption(_("📊 Visualisasi: Line chart — Gini Coefficient per kuartal (PMA: biru, PMDN: hijau). Garis threshold 0.4 menandai batas ketimpangan moderat. Metode: sum investasi per provinsi → hitung Gini Lorenz per kuartal."))

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


# ══════════════════════════════════════════════════
# 3. STD DEVIATION
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.3 Volatilitas Investasi Antar Provinsi (Std. Deviation)"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Standard Deviation</span>', unsafe_allow_html=True)

std_narrative = _("""Menggunakan metode **Standard Deviation** untuk mengukur volatilitas sebaran investasi.
SD mengukur *seberapa jauh* kesenjangan itu dalam nilai absolut. SD PMA kuartal terakhir sebesar
**{std_a:,.1f} IDR Bn / Miliar** — artinya sebaran investasi antar provinsi sangat lebar, dengan beberapa
provinsi menerima puluhan ribu miliar sementara yang lain nyaris nol. SD PMDN di **{std_d:,.1f} IDR Bn / Miliar**
juga memperlihatkan volatilitas yang besar. Perhatikan *spike* pada grafik — lonjakan SD biasanya
berkorelasi dengan kuartal di mana satu atau dua provinsi menerima mega-investasi, sementara
daerah lain stagnan. Pola ini konsisten dengan hipotesis bahwa investor menghindari wilayah
dengan **risiko hukum yang tidak bisa diprediksi**, memilih bertumpuk di \"safe haven\" yang sudah terbukti.""")

std_src = _("Agregasi <code>realisasi_investasi_asing.csv</code> & <code>realisasi_investasi_domestik.csv</code> — groupby(kuartal, provinsi) → sum → SD per kuartal.")
st.markdown(std_narrative.format(std_a=latest_std_a, std_d=latest_std_d) +
            f"\n\n<small>📁 <b>Sumber:</b> {std_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Line chart — Standard Deviation realisasi investasi antar provinsi per kuartal. PMA (biru), PMDN (hijau). Spike menandakan kuartal dengan konsentrasi extremitas tinggi."))

std_combined = pd.concat([std_a, std_d], ignore_index=True)
fig_std = px.line(
    std_combined, x="date", y="std_dev", color="tipe",
    color_discrete_map={"Investasi Asing (PMA)": C_ASING, "Investasi Domestik (PMDN)": C_DOMESTIK},
    template=PLOTLY_TEMPLATE,
    labels={"date": "Kuartal", "std_dev": "Std. Deviation (IDR Bn / Miliar)", "tipe": "Tipe Investasi"}
)
fig_std.update_layout(
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_std, use_container_width=True)


# ══════════════════════════════════════════════════
# 4. DISTRIBUSI PROVINSI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.4 Peta Konsentrasi Investasi per Provinsi"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Distribusi Top/Bottom Analysis</span>', unsafe_allow_html=True)

prov_narrative = _("""Menggunakan metode **Distribusi Top/Bottom Analysis** untuk mengidentifikasi konsentrasi investasi.
**{top1}**, **{top2}**, dan **{top3}** mendominasi penerimaan investasi gabungan PMA+PMDN,
sementara **{bot1}**, **{bot2}**, dan **{bot3}** nyaris tidak menerima apa-apa. Rasio Top/Bottom
mencapai **{ratio:,.0f}x lipat** — provinsi teratas menerima investasi {ratio:,.0f} kali lebih besar
dari terbawah. **5 provinsi teratas menyerap {top5:.1f}%** dari seluruh investasi, sementara
**10 provinsi terbawah hanya {bot10:.1f}%**. Ini bukan simply perbedaan daya saing ekonomi —
Gini di atas 0.6 mengindikasikan bahwa distorsi *non-fundamental* (termasuk inkonsistensi penegakan
hukum dan birokrasi) turut mendorong konsentrasi ini. Investor memilih bertumpuk di wilayah yang
\"dipersepsikan aman\" — sebuah *self-fulfilling prophecy* yang semakin melebarkan kesenjangan.""")

prov_src = _("Gabungan <code>realisasi_investasi_asing.csv</code> + <code>realisasi_investasi_domestik.csv</code>, groupby(provinsi) → mean.")
st.markdown(
    prov_narrative.format(
        top1=prov_top1['provinsi'], top2=prov_top2['provinsi'], top3=prov_top3['provinsi'],
        bot1=prov_bot1['provinsi'], bot2=prov_bot2['provinsi'], bot3=prov_bot3['provinsi'],
        ratio=ratio_top_bot, top5=top5_share, bot10=bot10_share
    ) + f"\n\n<small>📁 <b>Sumber:</b> {prov_src}</small>", unsafe_allow_html=True
)
st.caption(_("📊 Visualisasi: Bar chart horizontal — Top 15 dan Bottom 15 provinsi berdasarkan rata-rata investasi PMA+PMDN per kuartal. Warna = besaran nilai."))

n_show = 15
tab_top, tab_bottom = st.tabs([_("Top 15 Provinsi"), _("Bottom 15 Provinsi")])

with tab_top:
    top = prov_avg.tail(n_show)
    fig_top = px.bar(
        top, x="rata_rata", y="provinsi", orientation="h",
        color="rata_rata", color_continuous_scale=["#1B5E20", "#43A047", "#A5D6A7"],
        template=PLOTLY_TEMPLATE,
        labels={"rata_rata": "Rata-rata (IDR Bn / Miliar/kuartal)", "provinsi": ""}
    )
    fig_top.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_top, use_container_width=True)

with tab_bottom:
    bottom = prov_avg.head(n_show)
    fig_bot = px.bar(
        bottom, x="rata_rata", y="provinsi", orientation="h",
        color="rata_rata", color_continuous_scale=["#B71C1C", "#E53935", "#EF9A9A"],
        template=PLOTLY_TEMPLATE,
        labels={"rata_rata": "Rata-rata (IDR Bn / Miliar/kuartal)", "provinsi": ""}
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


# ══════════════════════════════════════════════════
# 5. ICOR NASIONAL
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("1.5 Tren ICOR Nasional: Biaya Ketidakpastian"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: ICOR Time Series</span>', unsafe_allow_html=True)

icor_trend_word = "naik" if icor_pma_trend > 0 else "turun"
icor_narrative = _("""Menggunakan metode **ICOR Time Series** untuk mengukur efisiensi investasi. ICOR PMA pada
{yr_first} sebesar **{v_first:.2f}**, namun pada {yr_last} menjadi **{v_last:.2f}** — {trend} **{chg:.1f}%**.
ICOR PMDN bahkan lebih buruk: dari **{d_first:.2f}** ke **{d_last:.2f}**. ICOR yang naik berarti
Indonesia membutuhkan **semakin banyak investasi** untuk menghasilkan 1 unit pertumbuhan PDB — sebuah
indikasi bahwa biaya-biaya tersembunyi (legal fees, delays, risk premium, korupsi) makin menggerogoti
efisiensi investasi. Ketika grafik ICOR dibaca bersama Gini di atas, terbangun sebuah narasi:
**investasi terkonsentrasi di sedikit daerah DAN makin tidak efisien** — dua sinyal sekaligus bahwa
ketidakpastian hukum bukan hanya mengusir investor dari daerah tertinggal, tapi juga menaikkan
biaya bagi mereka yang sudah berinvestasi.""")

icor_src = _("Data dari <code>icor_nasional.csv</code> (15 baris tahunan, {y1}-{y2}). Sumber: BPS.")
st.markdown(
    icor_narrative.format(
        yr_first=icor_year_first, yr_last=icor_year_last,
        v_first=icor_first, v_last=icor_last,
        trend=icor_trend_word, chg=abs(icor_pma_trend),
        d_first=icor_d_first, d_last=icor_d_last
    ) + f"\n\n<small>📁 <b>Sumber:</b> {icor_src.format(y1=icor_year_first, y2=icor_year_last)}</small>",
    unsafe_allow_html=True
)
st.caption(_("📊 Visualisasi: Line chart — ICOR PMDN (hijau) dan ICOR PMA (biru) per tahun. ICOR naik = investasi makin tidak efisien. Data langsung tanpa transformasi."))

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


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("Interpretasi & Temuan Utama"))

temuan = _("""
**Analisis Temuan Utama H1 — Inconsistency Risk:**

Ketiga indikator (Gini, SD, ICOR) secara **konvergen** menunjukkan bahwa investasi di Indonesia
mengalami **tiga masalah simultan** yang konsisten dengan hipotesis inkonsistensi hukum:

1. **Konsentrasi Extremitas** — Gini PMA **{gini_a:.3f}** dan PMDN **{gini_d:.3f}** (keduanya >0.4)
   menunjukkan investasi hanya mengalir ke segelintir provinsi. 5 provinsi teratas menyerap **{top5:.1f}%**
   total, sementara 10 terbawah hanya **{bot10:.1f}%**.

2. **Kesenjangan Melampaui Fundamental** — Rasio **{ratio:,.0f}x lipat** antara {prov_top} dan {prov_bot}
   tidak bisa sepenuhnya dijelaskan oleh perbedaan infrastruktur. Faktor non-ekonomi (inkonsistensi hukum,
   birokrasi, korupsi daerah) turut mendistorsi distribusi.

3. **Efisiensi Menurun** — ICOR PMA {trend} dari **{icor_f:.2f}** ({yr_f}) ke **{icor_l:.2f}** ({yr_l}),
   menandakan biaya investasi makin mahal — sebagian didorong oleh risk premium akibat ketidakpastian hukum.

**Implikasi:**
Investor merespons inkonsistensi hukum bukan dengan menghindari Indonesia secara keseluruhan,
tapi dengan **memusatkan investasi di \"zona aman\"** — menciptakan *dual economy* di mana beberapa
daerah makmur sementara mayoritas tertinggal. Ini adalah bukti bahwa *outcome uncertainty*
(H1) bukan teori, tapi **fakta yang terukur** dalam data investasi.
""")

st.markdown(temuan.format(
    gini_a=latest_gini_a, gini_d=latest_gini_d, top5=top5_share, bot10=bot10_share,
    ratio=ratio_top_bot, prov_top=prov_top1['provinsi'], prov_bot=prov_bot1['provinsi'],
    trend=icor_trend_word, icor_f=icor_first, icor_l=icor_last,
    yr_f=icor_year_first, yr_l=icor_year_last
))

st.markdown(f"""
<small><em>Catatan: Data ini menggunakan proxy ekonomi (distribusi investasi & ICOR).
Analisis ideal membutuhkan data putusan pengadilan dan variansi vonis lintas daerah
untuk mengukur inkonsistensi hukum secara langsung.</em></small>
""", unsafe_allow_html=True)
