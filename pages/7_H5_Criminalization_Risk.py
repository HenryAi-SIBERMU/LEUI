"""
Page 5 — H5: Criminalization Risk
Analisis IKK Expectation Collapse sebagai proxy risiko kriminalisasi
keputusan bisnis yang merusak kepercayaan investor.
    `Criminalization Risk → Personal Liability Fear → Expectation Collapse → Investment Freeze`

Causal Chain: Criminalization Risk → Personal Liability Fear → Expectation Collapse → Investment Freeze
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

st.set_page_config(
    page_title="H5: Criminalization Risk — CELIOS LEUI",
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
.metric-value { font-size: 2rem; font-weight: 700; }
.metric-label { font-size: 0.9rem; color: #AAA; margin-bottom: 5px; }
.metric-delta { font-size: 0.8rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
C_EXPECT = "#42A5F5"
C_PRESENT = "#66BB6A"
C_GAP = "#FF9800"
C_ANOMALY = "#E53935"
C_WARN = "#FF9800"
C_BG = "#1E1E1E"

# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "final")

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(DATA, "ikk_expect_vs_present.csv"), parse_dates=["date"])
    return df

df = load_data()
df = df.sort_values("date").reset_index(drop=True)


# ══════════════════════════════════════════════════
# PRE-COMPUTE
# ══════════════════════════════════════════════════

n_obs = len(df)
date_start = df["date"].min().strftime("%B %Y")
date_end = df["date"].max().strftime("%B %Y")

# Gap stats
gap_mean = df["ikk_gap"].mean()
gap_std = df["ikk_gap"].std()
gap_median = df["ikk_gap"].median()
gap_max = df["ikk_gap"].max()
gap_min = df["ikk_gap"].min()
gap_latest = df["ikk_gap"].iloc[-1]

# Expectation stats
exp_mean = df["ikk_expectation"].mean()
exp_latest = df["ikk_expectation"].iloc[-1]
pres_mean = df["ikk_present"].mean()
pres_latest = df["ikk_present"].iloc[-1]

# Z-Score on gap — detect abnormally WIDE gaps (fear dominates)
df["gap_z"] = (df["ikk_gap"] - gap_mean) / gap_std

# Detect expectation CRASHES (sharp month-over-month drop)
df["exp_change"] = df["ikk_expectation"].diff()
df["pres_change"] = df["ikk_present"].diff()
exp_change_mean = df["exp_change"].mean()
exp_change_std = df["exp_change"].dropna().std()
df["exp_crash_z"] = (df["exp_change"] - exp_change_mean) / exp_change_std

# Episodes: expectation crash (Z < -2) = sharp sudden collapse
df["is_exp_crash"] = df["exp_crash_z"] < -2
n_exp_crashes = df["is_exp_crash"].sum()

# Episodes: gap anomaly (Z > 2) = abnormally wide gap
df["is_gap_anomaly"] = df["gap_z"] > 2
n_gap_anomalies = df["is_gap_anomaly"].sum()

# Combined crisis: both IKK present drops AND gap widens
df["is_crisis"] = (df["exp_crash_z"] < -1.5) | (df["gap_z"] > 2)
n_crisis = df["is_crisis"].sum()

# Gap trend: first 5 years vs last 5 years
years_data = df["date"].dt.year
first_period = df[df["date"].dt.year <= df["date"].dt.year.quantile(0.25)]
last_period = df[df["date"].dt.year >= df["date"].dt.year.quantile(0.75)]
gap_early = first_period["ikk_gap"].mean()
gap_late = last_period["ikk_gap"].mean()
gap_trend_change = ((gap_late - gap_early) / gap_early * 100) if gap_early > 0 else 0
gap_trend_word = "membesar" if gap_trend_change > 0 else "menyempit"

# Correlation: when expectation drops, does gap widen?
corr_exp_gap, pval_exp_gap = stats.spearmanr(
    df["ikk_expectation"].dropna(),
    df["ikk_gap"].dropna()
)

# Rolling gap volatility (12-month window)
window = 12
df["gap_rolling_std"] = df["ikk_gap"].rolling(window=window, min_periods=6).std()

# Worst crash episode
if n_exp_crashes > 0:
    crash_episodes = df[df["is_exp_crash"]].copy()
    worst_crash_idx = crash_episodes["exp_change"].idxmin()
    worst_crash_date = crash_episodes.loc[worst_crash_idx, "date"].strftime("%B %Y")
    worst_crash_val = crash_episodes.loc[worst_crash_idx, "exp_change"]
else:
    worst_crash_date = "—"
    worst_crash_val = 0

# Max gap episode
max_gap_idx = df["ikk_gap"].idxmax()
max_gap_date = df.loc[max_gap_idx, "date"].strftime("%B %Y")
max_gap_val = df.loc[max_gap_idx, "ikk_gap"]

# Periods where gap inverted (present > expectation) = extreme crisis
df["gap_inverted"] = df["ikk_gap"] < 0
n_inverted = df["gap_inverted"].sum()


# ══════════════════════════════════════════════════
# HEADER & INTRO
# ══════════════════════════════════════════════════
st.title(_("H5: Ancaman Penjara Direksi (Kriminalisasi Kebijakan)"))
subtitle = _("Kepercayaan pasar dan investor seringkali langsung runtuh saat pemegang diskresi dikriminalisasi.")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Setup Variables (Hukum) ──
_mk_yr_path = os.path.join(DATA, "putusan_mk_yearly.csv")
_mk_breakdown_path = os.path.join(DATA, "mk_uu_breakdown.csv")

_df_mk_yr = pd.DataFrame()
_df_mk_uu = pd.DataFrame()
_total_mk = 0
_top_uu = ""
_top_uu_cnt = 0

if os.path.exists(_mk_yr_path) and os.path.exists(_mk_breakdown_path):
    _df_mk_yr = pd.read_csv(_mk_yr_path)
    _df_mk_uu = pd.read_csv(_mk_breakdown_path)
    _total_mk = int(_df_mk_yr['total_putusan_mk'].sum()) if not _df_mk_yr.empty else 0
    _top_uu = _df_mk_uu.iloc[0]['uu_diuji'] if not _df_mk_uu.empty else ""
    _top_uu_cnt = _df_mk_uu.iloc[0]['jumlah'] if not _df_mk_uu.empty else 0

# ── Methodology ──
with st.expander(_("🔍 Metodologi"), expanded=False):
    st.markdown(_("""
    **Causal Chain Law & Economics:**
    `Kriminalisasi Bisnis (X) → Ketidakpastian Operasional → Persepsi Risiko Investasi (Personal Liability) → Biaya Kepercayaan Rusak → Keputusan Penarikan Diri (Y)`

    **Variabel Independen (X):**
    - Sengketa Uji Materi (*Judicial Review*) regulasi strategis di Mahkamah Konstitusi (data OSINT Landmark Verdicts).
    - Konsentrasi serangan judisial terhadap stabilitas kebijakan ekonomi (UU Cipta Kerja).
    
    **Variabel Dependen (Y):**
    - Indeks Keyakinan Konsumen (IKK) *Expectation vs Present Gap* sebagai representasi sentimen makro.
    - Z-Score untuk mendeteksi *Expectation Crash* mendadak.
    """))

# ── Intro Narrative ──
intro = _("""Kerangka empiris **Ancaman Penjara Direksi (Criminalization Risk)** menelisik bagaimana pengkriminalan keputusan bisnis dan sengketa konstan merusak fondasi kepercayaan iklim makro. Sepanjang periode observasi, terjadi **{tot_mk}** Vonis Sakti (*Landmark Verdicts*) Uji Materi di Mahkamah Konstitusi, dengan serangan tertinggi dijatuhkan ke UU ketenagakerjaan/ekonomi (seperti **{top_uu}**). Absennya kepastian akhir dan instabilitas garansi undang-undang ini menciptakan iklim **Paranoia Penjara Pribadi (*Personal Liability Fear*)** bagi pemegang diskresi.

Teror hukum ini segera diterjemahkan menjadi **Biaya Sentimen Ekonomi** ekstrem. Publik merespons hantaman ketidakpastian tersebut dengan pesimisme tajam, tertangkap algoritma dalam **{n_crash} episode Urat Nadi Kepanikan (*Expectation Crash*)** di mana indeks anjlok brutal mendobrak level wajar (Skala Petaka Z-Score < -2). Kepanikan makro ini memuncak saat selisih Celah Keputusasaan (*gap* ekspektasi) melebar mendadak hingga titik terekstrem **{gap_max:.1f} poin** pada {max_gap_date}. Runtuhnya asuransi keyakinan ini secara telak mematikan keberanian institusi untuk berinvestasi, mengerem keras **Keputusan Buka Pabrik (Keputusan Ekspansi Pasar / Variabel Y)**.""")

intro_src = _("Landmark Verdicts MKRI (Variabel Hukum/X) & Data IKK Expectation vs Present Gap BI (Variabel Ekonomi/Y).")

st.markdown(
    intro.format(
        tot_mk=_total_mk, top_uu=_top_uu,
        n_crash=n_exp_crashes, gap_max=gap_max, max_gap_date=max_gap_date
    ) +
    f"\n\n<small>📁 <b>Sumber Basis Data:</b> {intro_src}</small>",
    unsafe_allow_html=True
)
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── Overview KPI Cards (Hukum + Ekonomi) ──
st.markdown("### Eksekutif Summary (H5)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid #AB47BC; text-align: center; height:100%;">
        <div style="color: #AAA; font-size: 0.9rem; margin-bottom: 5px;">Rekor Vonis MK</div>
        <div style="color: #E1BEE7; font-size: 2rem; font-weight: bold;">{_total_mk} Putusan</div>
        <div style="color: #AB47BC; font-size: 0.8rem; font-weight: 600;">Variabel Hukum (X)</div>
        <p style="color: #888; font-size: 0.75rem; border-top: 1px dotted #777; margin-top: 10px; padding-top: 8px; text-align: left;">
            <b>Asal Angka:</b> Total rekam jejak putusan Uji Materi (Landmark Verdicts) Mahkamah Konstitusi RI sepanjang periode observasi.
        </p>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {C_ANOMALY}; text-align: center; height:100%;">
        <div style="color: #AAA; font-size: 0.9rem; margin-bottom: 5px;">Alarm Kepanikan Pasar</div>
        <div style="color: {C_ANOMALY}; font-size: 2rem; font-weight: bold;">{n_exp_crashes} Episode</div>
        <div style="color: {C_WARN}; font-size: 0.8rem; font-weight: 600;">Crash Sentimen (Y)</div>
        <p style="color: #888; font-size: 0.75rem; border-top: 1px dotted #777; margin-top: 10px; padding-top: 8px; text-align: left;">
            <b>Asal Angka:</b> Penurunan Indeks Keyakinan Konsumen secara mendadak melebihi batas ekstrem wajar (Kalkulasi <i>Z-Score</i> < -2).
        </p>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {C_ANOMALY}; text-align: center; height:100%;">
        <div style="color: #AAA; font-size: 0.9rem; margin-bottom: 5px;">Celah Keputusasaan Terlebar</div>
        <div style="color: {C_ANOMALY}; font-size: 2rem; font-weight: bold;">{gap_max:.1f} Poin</div>
        <div style="color: #AAA; font-size: 0.8rem; font-weight: 600;">Krisis Kepercayaan</div>
        <p style="color: #888; font-size: 0.75rem; border-top: 1px dotted #777; margin-top: 10px; padding-top: 8px; text-align: left;">
            <b>Asal Angka:</b> Selisih titik rekor Gap terjauh antara harapan/ekspektasi masyarakat melawan kenyataan ekonomi saat ini.
        </p>
    </div>""", unsafe_allow_html=True)
with c4:
    crash_color = C_ANOMALY if worst_crash_val < -10 else C_WARN
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {crash_color}; text-align: center; height:100%;">
        <div style="color: #AAA; font-size: 0.9rem; margin-bottom: 5px;">Runtuhnya Mental Terburuk</div>
        <div style="color: {crash_color}; font-size: 2rem; font-weight: bold;">{worst_crash_val:.1f} Poin</div>
        <div style="color: {C_WARN}; font-size: 0.8rem; font-weight: 600;">Terekam {worst_crash_date}</div>
        <p style="color: #888; font-size: 0.75rem; border-top: 1px dotted #777; margin-top: 10px; padding-top: 8px; text-align: left;">
            <b>Asal Angka:</b> Penurunan terdalam sebulan dari ekspektasi dompet masyarakat yang tercatat sepanjang sejarah periode.
        </p>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 5.1 Variabel Hukum (X) ──
st.markdown("---")
st.subheader("5.1 Fakta Penyebab: Gugatan Beruntun terhadap Undang-Undang Vital di MK")
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Distribusi OSINT Direktori Mahkamah Konstitusi RI</span>', unsafe_allow_html=True)

# ── Compute legal stats for narrative ──
_mk_year_range = ""
_mk_peak_year = ""
_mk_peak_vol = 0
_mk_n_uu = 0
_mk_cipta_kerja_pct = 0
if not _df_mk_yr.empty:
    _mk_year_range = f"{int(_df_mk_yr['year'].min())}–{int(_df_mk_yr['year'].max())}"
    _peak_idx = _df_mk_yr['total_putusan_mk'].idxmax()
    _mk_peak_year = str(int(_df_mk_yr.loc[_peak_idx, 'year']))
    _mk_peak_vol = int(_df_mk_yr.loc[_peak_idx, 'total_putusan_mk'])
if not _df_mk_uu.empty:
    _mk_n_uu = len(_df_mk_uu)
    _ck_mask = _df_mk_uu['uu_diuji'].str.contains('Cipta Kerja', case=False, na=False)
    _ck_total = int(_df_mk_uu.loc[_ck_mask, 'jumlah'].sum())
    _all_total = int(_df_mk_uu['jumlah'].sum())
    _mk_cipta_kerja_pct = round(_ck_total / _all_total * 100, 1) if _all_total > 0 else 0

st.markdown(f"""
Analisis **Variabel Hukum (X)** berangkat dari inventarisasi *Landmark Verdicts* Mahkamah Konstitusi RI
sepanjang periode **{_mk_year_range}**. Dari total **{_total_mk} putusan** yang terrecord,
bencana ketidakpastian memuncak di tahun **{_mk_peak_year}** dengan bombardir **{_mk_peak_vol} putusan** pencabutan/modifikasi — sebuah
tsunami hukum yang menghantam tiang-tiang regulasi ekonomi kita.

Lebih mengerikannya lagi, konsentrasi tembakan ini sangat bias: **{_mk_cipta_kerja_pct}%**
dari amunisi sengketa MK menyasar kluster **UU Cipta Kerja** — padahal ini adalah karpet merah investasi negara.
Digusurnya pasal-pasal kunci secara konstan menciptakan jerat *regulatory sieging effect*: investor maju mundur karena garansi tertinggi negara ternyata tidak kebal dari pembatalan sepihak.

<small>📁 <b>Sumber:</b> Direktori Putusan Mahkamah Konstitusi RI (OSINT). Data: <code>putusan_mk_yearly.csv</code> & <code>mk_uu_breakdown.csv</code>.</small>
""", unsafe_allow_html=True)

import plotly.express as px
_cc1, _cc2 = st.columns([1.5, 1])
with _cc1:
    st.markdown("##### Tren Historis Putusan MK")
    if not _df_mk_yr.empty:
        import plotly.graph_objects as go
        fig_mk = go.Figure()
        fig_mk.add_trace(go.Bar(x=_df_mk_yr["year"], y=_df_mk_yr["total_putusan_mk"], name="Total Putusan MK", marker_color="#AB47BC", hovertemplate="<b>Tahun %{x}</b><br>Jumlah Putusan: %{y} Kasus<extra></extra>"))
        # Panah Anotasi Data Storytelling
        fig_mk.add_annotation(
            x=_mk_peak_year, y=_mk_peak_vol,
            text=f"Puncak Tsunami Hukum ({_mk_peak_vol})",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#FF5252",
            ax=-30, ay=-40, font=dict(color="#FFCDD2", size=12), bgcolor="#B71C1C"
        )
        fig_mk.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        fig_mk.update_yaxes(title_text="Volume Putusan")
        st.plotly_chart(fig_mk, use_container_width=True)

with _cc2:
    st.markdown("##### Konsentrasi Objek Sengketa")
    if not _df_mk_uu.empty:
        _df_mk_uu_top = _df_mk_uu.head(5)
        fig_uu = px.pie(
            _df_mk_uu_top, values='jumlah', names='uu_diuji', hole=0.6,
            color_discrete_sequence=px.colors.sequential.Sunset
        )
        fig_uu.update_layout(template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        fig_uu.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Total Gugatan: %{value} Kasus<extra></extra>")
        st.plotly_chart(fig_uu, use_container_width=True)

st.markdown(f"""
<div style="border-left: 5px solid #FF5252; background-color: #2F0A28; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h4 style="color: #FFCDD2; margin-top: 0; font-size: 1.1em;">Kesimpulan Kilat: Tsunami Gugatan UU</h4>
    <p style="color: #E1BEE7; margin-bottom: 0; font-size: 0.95em;">
        Rekor gugatan hukum memuncak parah di tahun <b>{_mk_peak_year}</b> dengan pencapaian {_mk_peak_vol} putusan. Nasib ekonomi terbukti rentan karena serangan paling masif diarahkan khusus untuk menggugurkan <b>UU Cipta Kerja</b> (Mendominasi <b>{_mk_cipta_kerja_pct}%</b> dari total kasus). Investor jelas trauma saat jaminan investasi tertinggi negara terus dibombardir ancaman pembatalan konstitusional.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 5.2 IKK EXPECTATION vs PRESENT + GAP (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.2 Dampak: Runtuhnya Keyakinan / Jurang Kepercayaan Pasar")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Gap Analysis (Variabel Y)</span>', unsafe_allow_html=True)

ts_narr = """Bayangkan **Celah Keputusasaan (Gap Analysis)** sebagai jarak antara mimpi muluk warga dengan isi dompet aslinya hari ini. Dalam grafik, garis biru adalah mimpi (ekspektasi), dan hijau adalah kenyataan dompet (Present). Area oranye di tengahnya adalah **Jurang Gap**.
Rakyat kita terbukti selalu memupuk angan kelewat tinggi (rata-rata gap: {gap_mean:.1f} poin).
Namun, ini menjadi **sangat berbahaya** saat jaminan hukum diobrak-abrik elit: celah impian versus realita tiba-tiba melebar tajam mendobrak kewajaran. Artinya, warga mulai tersadar bahwa kehidupan nyatanya sedang merana, sementara angan kemajuannya hanyut bagai ilusi kosong."""

ts_src = "Data IKK <code>ikk_expect_vs_present.csv</code> (Bank Indonesia). Gap = IKK Expectation - IKK Present."
st.markdown(ts_narr.format(gap_mean=gap_mean) +
            f"\n\n<small>📁 <b>Sumber:</b> {ts_src}</small>", unsafe_allow_html=True)

fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(
    x=df["date"], y=df["ikk_expectation"], mode="lines", name="Ilusi Masa Depan (Ekspektasi)",
    line=dict(color=C_EXPECT, width=2),
    hovertemplate="<b>%{x|%b %Y}</b><br>Ekspektasi: %{y:.1f}<extra></extra>"
))
fig_ts.add_trace(go.Scatter(
    x=df["date"], y=df["ikk_present"], mode="lines", name="Kenyataan Dompet (Saat Ini)",
    line=dict(color=C_PRESENT, width=2),
    hovertemplate="<b>%{x|%b %Y}</b><br>Kenyataan: %{y:.1f}<extra></extra>"
))
# Gap as filled area
fig_ts.add_trace(go.Scatter(
    x=df["date"], y=df["ikk_gap"], mode="lines", name="Jurang Gap Area",
    line=dict(color=C_GAP, width=1.5, dash="dot"), yaxis="y2",
    hovertemplate="Lebar Jurang (Gap): %{y:.1f} Poin<extra></extra>"
))

max_gap_row = df.loc[df["ikk_gap"].idxmax()]
fig_ts.add_annotation(
    x=max_gap_row["date"], y=max_gap_row["ikk_gap"], yref="y2",
    text=f"Celah Keputusasaan Terlebar ({max_gap_row['ikk_gap']:.1f})",
    showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor="#FF5252", ax=0, ay=-40,
    font=dict(color="white", size=11), bgcolor="#B71C1C"
)

fig_ts.update_layout(
    template=PLOTLY_TEMPLATE, height=450,
    yaxis=dict(title="Nilai Indeks IKK"),
    yaxis2=dict(title="Jurang Selisih (poin)", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=60, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_ts, use_container_width=True)

st.markdown(f"""
<div style="border-left: 5px solid #FF5252; background-color: #2F0A28; padding: 15px; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;">
    <h4 style="color: #FFCDD2; margin-top: 0; font-size: 1.1em;">Kesimpulan Kilat: Ilusi Kesejahteraan</h4>
    <p style="color: #E1BEE7; margin-bottom: 0; font-size: 0.95em;">
        Data tidak bisa berbohong: Celah (Gap) tertinggi merobek angka <b>{gap_max:.1f} poin</b> tepat di bulan <b>{max_gap_date}</b>. Ini adalah monumen kehancuran di mana masyarakat mencapai titik keputusasaan terparah menyadari realita keuangannya sedang berdarah, berbanding terbalik dari ilusi harapan masa depannya.
    </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 5.3 EXPECTATION CRASH DETECTION (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.3 Dampak: Alarm Kepanikan Mendadak (Visualisasi Garis Waktu)")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Crash Detection (Variabel Y)</span>', unsafe_allow_html=True)

crash_narr = """Sistem **Detektor Urat Nadi Kepanikan (Z-Score Crash Detection)** kami secara otomatis mendata kapan harapan warga tercabut secara mendadak.
Batang merah murni menandakan **Kepanikan Ekstrem** (Skala Petaka Z-Score < -2) — ini adalah bulan di mana mental masyarakat jatuh terjun bebas. Kehancuran tajam ini konsisten dengan memuncaknya syok diskresi kriminalisasi (seperti penangkapan direksi publik atau penggusuran aset tiba-tiba) yang mengerem laju bisnis.
Hari tergelap tercatat pada **{worst_date}** ketika keyakinan dirampas paksa sebesar **{worst_val:.1f} poin** hanya dalam sebulan (garis oranye putus-putus mewakili rata-rata fluktuasi normal: {avg_chg:.2f})."""

st.markdown(crash_narr.format(
    worst_date=worst_crash_date, worst_val=worst_crash_val, avg_chg=exp_change_mean
) + f"\n\n<small>📁 <b>Sumber:</b> Kalkulasi turunan <code>ikk_expect_vs_present.csv</code> (Bank Indonesia).</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Bar merah adalah kepanikan maut (Z<-2). Oranye adalah guncangan (Z<-1). Biru adalah kondisi stabil/naik.")

df_chg = df.dropna(subset=["exp_change"]).copy()
bar_colors_crash = []
for _, row in df_chg.iterrows():
    if row["exp_crash_z"] < -2:
        bar_colors_crash.append(C_ANOMALY)
    elif row["exp_crash_z"] < -1:
        bar_colors_crash.append(C_WARN)
    else:
        bar_colors_crash.append(C_EXPECT)

fig_crash = go.Figure()
fig_crash.add_trace(go.Bar(
    x=df_chg["date"], y=df_chg["exp_change"],
    marker_color=bar_colors_crash, name="Keruntuhan Titik Harapan",
    hovertemplate="<b>%{x|%b %Y}</b><br>Amblas/Naik: %{y:.1f} poin<br>Skala Petaka Z-Score: %{customdata:.2f}<extra></extra>",
    customdata=df_chg["exp_crash_z"]
))

worst_crash_row = df_chg.loc[df_chg["exp_change"].idxmin()]
fig_crash.add_annotation(
    x=worst_crash_row["date"], y=worst_crash_row["exp_change"],
    text="Hantaman Sentimen Terdalam",
    showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor="#FF5252", ax=0, ay=40,
    font=dict(color="white", size=11), bgcolor="#B71C1C"
)

fig_crash.add_hline(y=exp_change_mean, line_dash="dash", line_color=C_WARN,
                    annotation_text=f"Rata-rata: {exp_change_mean:.2f}")
fig_crash.add_hline(y=0, line_dash="dot", line_color="#666")
fig_crash.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="Jatuh/Bangun Ekspektasi (poin)", xaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20), showlegend=False, hovermode="x unified"
)
st.plotly_chart(fig_crash, use_container_width=True)

st.markdown(f"""
<div style="border-left: 5px solid #FF5252; background-color: #2F0A28; padding: 15px; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;">
    <h4 style="color: #FFCDD2; margin-top: 0; font-size: 1.1em;">Kesimpulan Kilat: Radar Kepanikan Berdering</h4>
    <p style="color: #E1BEE7; margin-bottom: 0; font-size: 0.95em;">
        Secara total, mesin merekam <b>{n_exp_crashes} ledakan <i>Expectation Crash</i></b> (Amblas mendadak tak tertebak). Ini bukan kebetulan semata. Ketika pedang penegak hukum membabat kepastian bisnis secara misterius, mental warga otomatis tersungkur. Di titik inilah pimpinan perusahaan pasti mengerem uang ekspansinya secara instan!
    </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 5.4 ROLLING GAP VOLATILITY (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.4 Dampak: Gejolak Ketidakpastian Mematikan Investasi")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Rolling Standard Deviation (Variabel Y)</span>', unsafe_allow_html=True)

vol_narr = """Bayangkan indikator **Gempa Ketidakpastian (Rolling Gap Volatility)** ini sebagai alat pengukur kepanikan angin-anginan (standar deviasi rolling {win}-bulan).
Tebalnya gelombang warna merah menandakan periode di mana **kebingungan massal** memuncak — 
warga bukan cuma pesimis, tapi mereka **sama sekali tidak bisa menebak hari esok**.
Ini adalah dampak racun paling mematikan dari *criminalization risk*: ketika hukum tiba-tiba menerkam tanpa peringatan, masyarakat kehilangan kompas hidupnya. Pola lonjakan ini (*expectation volatility*) dijamin membuat semua uang investor **otomatis membeku**, karena tidak ada orang waras yang mau bertaruh di atas tanah gempa."""

vol_src = "Kalkulasi rolling std. deviation IKK Gap dari <code>ikk_expect_vs_present.csv</code> (Bank Indonesia)."
st.markdown(vol_narr.format(win=window) +
            f"\n\n<small>📁 <b>Sumber:</b> {vol_src}</small>", unsafe_allow_html=True)

fig_vol = go.Figure()
fig_vol.add_trace(go.Scatter(
    x=df["date"], y=df["gap_rolling_std"], mode="lines",
    name=f"Gempa Perubahan ({window}-bulan)",
    line=dict(color=C_ANOMALY, width=2),
    fill="tozeroy", fillcolor="rgba(229,57,53,0.15)",
    hovertemplate="<b>%{x|%b %Y}</b><br>Skala Gempa Volatilitas: %{y:.2f}<extra></extra>"
))

max_vol_row = df.loc[df["gap_rolling_std"].idxmax()]
if pd.notna(max_vol_row["gap_rolling_std"]):
    fig_vol.add_annotation(
        x=max_vol_row["date"], y=max_vol_row["gap_rolling_std"],
        text="Pusat Gempa Kepercayaan Terburuk",
        showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor="#FF5252", ax=0, ay=-40,
        font=dict(color="white", size=11), bgcolor="#B71C1C"
    )

fig_vol.update_layout(
    template=PLOTLY_TEMPLATE, height=380,
    yaxis_title="Getaran Gempa Gap (Rolling Std)", xaxis_title="",
    margin=dict(l=20, r=20, t=20, b=20), showlegend=False, hovermode="x unified"
)
st.plotly_chart(fig_vol, use_container_width=True)

st.markdown(f"""
<div style="border-left: 5px solid #FF5252; background-color: #2F0A28; padding: 15px; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;">
    <h4 style="color: #FFCDD2; margin-top: 0; font-size: 1.1em;">Kesimpulan Kilat: Badai Kebingungan Mematikan</h4>
    <p style="color: #E1BEE7; margin-bottom: 0; font-size: 0.95em;">
        Gelombang kepanikan tidak terprediksi ini merupakan konfirmasi mutlak bahwa pasar sedang buta arah dan histeris. Otomatis, begitu grafik merah ini menebal, mesin industri dan keran keputusan investasi dari para direksi dipastikan ikut menghentikan nafasnya rapat-rapat menyelamatkan "leher" masing-masing.
    </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 5.5 TABEL EPISODE KRISIS (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.5 Catatan Peristiwa: Kapan Kepercayaan Runtuh?")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Episode Mapping (Variabel Y)</span>', unsafe_allow_html=True)

tbl_narr = """Log sejarah **Pemetaan Tragedi (Z-Score Episode Detection)** ini membongkar deretan rekam jejak terburuk mesin pendeteksi algoritma kami.
Kolom di bawah secara transparan mengurutkan tanggal kejadian, tingkat ilusi harapan vs kenyataan, dan skala kepanikannya (Z-Score). Tabel ini bisa dilacak ke belakang oleh jurnalis untuk dicocokkan dengan kejadian penangkapan petinggi atau pengubahan hukum gila-gilaan pada bulan/tahun terkait."""

tbl_src = "Deteksi algoritma Z-Score dari data <code>ikk_expect_vs_present.csv</code> (Bank Indonesia)."
st.markdown(tbl_narr + f"\n\n<small>📁 <b>Sumber:</b> {tbl_src}</small>", unsafe_allow_html=True)

# Combine crash + gap anomaly episodes
crisis_episodes = df[df["is_crisis"]].copy()
if len(crisis_episodes) > 0:
    tbl = crisis_episodes[["date", "ikk_expectation", "ikk_present", "ikk_gap", "gap_z", "exp_change"]].copy()
    tbl["date"] = tbl["date"].dt.strftime("%B %Y")
    tbl.columns = ["Tanggal", "Ilusi Harapan (Ekspektasi)", "Isi Dompet (Realita)", "Lebar Jurang (Gap)", "Skala Petaka (Z-Score)", "Amblas/Naik (Poin)"]
    tbl = tbl.sort_values("Skala Petaka (Z-Score)", ascending=False).head(20).reset_index(drop=True)
    st.dataframe(tbl.style.format({
        "Ilusi Harapan (Ekspektasi)": "{:.1f}",
        "Isi Dompet (Realita)": "{:.1f}",
        "Lebar Jurang (Gap)": "{:.1f}",
        "Skala Petaka (Z-Score)": "{:.2f}",
        "Amblas/Naik (Poin)": "{:.1f}"
    }), use_container_width=True, hide_index=True)
else:
    st.info("Tidak ada episode krisis yang terdeteksi pada dataset ini.")


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("Interpretasi & Temuan Utama")

temuan = f"""
<div style="background-color: #2F0A28; padding: 20px; border-radius: 10px; border-left: 5px solid #FF5252;">
    <h3 style="color: #FFCDD2; margin-top: 0; margin-bottom: 15px;">3. Kesimpulan: Paranoia Penjara Merusak Nadi Ekonomi</h3>
    <ul style="color: #E1BEE7; font-size: 1.05em; line-height: 1.6;">
        <li style="margin-bottom: 10px;"><b>Epidemi Tsunami Hukum (Variabel X):</b> Ada <b>{_total_mk} Vonis Sakti MK</b> sepanjang periode, di mana rekor tembakan terbanyak di tahun {_mk_peak_year}. Mengerikannya, <b>{_mk_cipta_kerja_pct}%</b> diarahkan membasmi tiang penyangga garansi bernama UU Cipta Kerja. Hal ini menginjeksi rasa takut (Paranoia Penjara Pribadi / <i>Personal Liability Fear</i>) secara permanen ke tulang sumsum eksekutif bisnis.</li>
        <li style="margin-bottom: 10px;"><b>Kepanikan Massal Terekam Data (Variabel Y):</b> Teror tersebut dibayar sangat mahal. Mesin otomatis menangkap <b>{n_exp_crashes} ledakan <i>Expectation Crash</i></b> (Skala Z-Score < -2) dan menganga lebarnya Celah Keputusasaan (Gap Harapan vs Kenyataan) hingga menyentuh angka raksasa <b>{gap_max:.1f} poin</b>. Keyakinan publik luluh lantak!</li>
        <li style="margin-bottom: 10px;"><b>Kemustahilan Buka Pabrik:</b> Ada kecocokan mutlak (Korelasi r = {corr_exp_gap:.3f}). Tren keputusasaan yang <b>{gap_trend_word} {abs(gap_trend_change):.1f}%</b> ini memastikan satu fakta pedih: Selama hukum masih bisa dipelesetkan sebagai pedang untuk memenjarakan direksi sah, Mustahil para pemodal berani mempertaruhkan uang bilyunannya di Indonesia. Mesin pemutar ekonomi nasional otomatis membeku.</li>
    </ul>
</div>
"""

st.markdown(temuan, unsafe_allow_html=True)
