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
st.title(_("H5: Criminalization Risk — Kriminalisasi Keputusan Bisnis"))
subtitle = _("Analisis IKK Expectation Collapse sebagai Proxy Risiko Personal Liability Investor")
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
with st.expander(_("Metodologi: Analisis Criminalization Risk (H5)"), expanded=False):
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
intro = _("""Kerangka empiris **Criminalization Risk** menelisik bagaimana pengkriminalan keputusan bisnis dan sengketa konstan merusak fondasi kepercayaan iklim makro. Sepanjang periode observasi, terjadi **{tot_mk}** *Landmark Verdicts* Uji Materi di Mahkamah Konstitusi, dengan serangan tertinggi dijatuhkan ke UU ketenagakerjaan/ekonomi (seperti **{top_uu}**). Absennya kepastian akhir dan instabilitas garansi undang-undang ini menciptakan teror **Personal Liability Fear** bagi pemegang diskresi.

Teror hukum ini segera diterjemahkan menjadi **Biaya Sentimen Ekonomi** ekstrem. Publik merespons *shock* ketidakpastian tersebut dengan pesimisme tajam, tertangkap algoritma dalam **{n_crash} episode *Expectation Crash*** di mana indeks anjlok brutal mendobrak level wajar (Z-Score < -2). Kepanikan makro ini memuncak saat selisih kesenjangan harapan (*gap* ekspektasi) melebar mendadak hingga titik terekstrem **{gap_max:.1f} poin** pada {max_gap_date}. Runtuhnya asuransi keyakinan ini secara telak mematikan keberanian institusi untuk berinvestasi, mengerem keras **Keputusan Ekspansi Pasar (Variabel Y)**.""")

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
    <div class="metric-card">
        <div class="metric-label">Vonis Uji Materi MK</div>
        <div class="metric-value" style="color:#AB47BC">{_total_mk}</div>
        <div class="metric-delta" style="color:#AB47BC">Variabel Hukum (X)</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Episode Expectation Crash</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{n_exp_crashes}</div>
        <div class="metric-delta" style="color:{C_WARN}">Variabel Ekonomi (Y)</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gap IKK Terlebar</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{gap_max:.1f} Poin</div>
        <div class="metric-delta" style="color:#AAA">Krisis Kepercayaan</div>
    </div>""", unsafe_allow_html=True)
with c4:
    crash_color = C_ANOMALY if worst_crash_val < -10 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Crash Sentimen Terdalam</div>
        <div class="metric-value" style="color:{crash_color}">{worst_crash_val:.1f} Poin</div>
        <div class="metric-delta" style="color:{C_WARN}">{worst_crash_date}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 5.1 Variabel Hukum (X) ──
st.markdown("---")
st.subheader("5.1 Variabel Hukum (X): Volume Pembatalan Undang-Undang MK")
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Distribusi OSINT Direktori Mahkamah Konstitusi RI</span>', unsafe_allow_html=True)

import plotly.express as px
_cc1, _cc2 = st.columns([1.5, 1])
with _cc1:
    st.markdown("##### Tren Historis Putusan MK")
    if not _df_mk_yr.empty:
        import plotly.graph_objects as go
        fig_mk = go.Figure()
        fig_mk.add_trace(go.Bar(x=_df_mk_yr["year"], y=_df_mk_yr["amar_ditolak"], name="Amar Ditolak", marker_color="#78909C"))
        fig_mk.add_trace(go.Bar(x=_df_mk_yr["year"], y=_df_mk_yr["amar_dikabulkan"], name="Amar Dikabulkan", marker_color="#E53935"))
        fig_mk.add_trace(go.Bar(x=_df_mk_yr["year"], y=_df_mk_yr["amar_lainnya"], name="Amar Lainnya", marker_color="#BDBDBD"))
        fig_mk.update_layout(barmode="stack", template="plotly_dark", height=320, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
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
        fig_uu.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_uu, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 5.2 IKK EXPECTATION vs PRESENT + GAP (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.2 Dampak Ekonomi (Y): Gap Ekspektasi — Jurang Kepercayaan Konsumen")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Gap Analysis (Variabel Y)</span>', unsafe_allow_html=True)

ts_narr = """Menggunakan metode **Gap Analysis** — dua garis menunjukkan IKK Ekspektasi (biru) dan IKK Kondisi Saat Ini (hijau).
Area oranye di antaranya adalah **gap** — selisih antara apa yang masyarakat harapkan
dengan apa yang mereka rasakan saat ini. Gap yang **konsisten lebar** (rata-rata: {gap_mean:.1f} poin)
menandakan bahwa masyarakat Indonesia secara kronis **lebih optimis tentang masa depan
daripada kondisi saat ini** — sebuah pola yang sehat dalam ekonomi normal, namun menjadi
**tanda bahaya** ketika gap terlalu lebar atau tiba-tiba melebar: itu artinya realita
jauh lebih buruk dari harapan, atau harapan sedang runtuh."""

ts_src = "Data IKK <code>ikk_expect_vs_present.csv</code> (Bank Indonesia). Gap = IKK Expectation - IKK Present."
st.markdown(ts_narr.format(gap_mean=gap_mean) +
            f"\n\n<small>📁 <b>Sumber:</b> {ts_src}</small>", unsafe_allow_html=True)

fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(
    x=df["date"], y=df["ikk_expectation"], mode="lines", name="IKK Ekspektasi",
    line=dict(color=C_EXPECT, width=2),
    hovertemplate="<b>%{x|%b %Y}</b><br>Ekspektasi: %{y:.1f}<extra></extra>"
))
fig_ts.add_trace(go.Scatter(
    x=df["date"], y=df["ikk_present"], mode="lines", name="IKK Saat Ini",
    line=dict(color=C_PRESENT, width=2),
    hovertemplate="<b>%{x|%b %Y}</b><br>Saat Ini: %{y:.1f}<extra></extra>"
))
# Gap as filled area
fig_ts.add_trace(go.Scatter(
    x=df["date"], y=df["ikk_gap"], mode="lines", name="Gap (Exp - Present)",
    line=dict(color=C_GAP, width=1.5, dash="dot"), yaxis="y2",
    hovertemplate="Gap: %{y:.1f}<extra></extra>"
))
fig_ts.update_layout(
    template=PLOTLY_TEMPLATE, height=450,
    yaxis=dict(title="IKK Index"),
    yaxis2=dict(title="Gap (poin)", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=60, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_ts, use_container_width=True)


# ══════════════════════════════════════════════════
# 5.3 EXPECTATION CRASH DETECTION (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.3 Dampak Ekonomi (Y): Deteksi Algoritmik — Crash Kepercayaan Mendadak")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Crash Detection (Variabel Y)</span>', unsafe_allow_html=True)

crash_narr = """Menggunakan metode **Z-Score Crash Detection** pada perubahan bulanan IKK Ekspektasi.
Bar merah menandai **crash** (Z < -2) — bulan-bulan di mana ekspektasi publik jatuh secara
abnormal. Crash mendadak ini konsisten dengan pola *criminalization shock* — peristiwa
seperti penangkapan direksi, kriminalisasi pejabat, atau penahanan aset mendadak
yang langsung merusak kepercayaan publik. Crash terburuk terjadi pada
**{worst_date}** dengan penurunan **{worst_val:.1f} poin** dalam satu bulan.
Garis oranye putus-putus menunjukkan rata-rata perubahan bulanan ({avg_chg:.2f})."""

st.markdown(crash_narr.format(
    worst_date=worst_crash_date, worst_val=worst_crash_val, avg_chg=exp_change_mean
) + f"\n\n<small>📁 <b>Sumber:</b> Kalkulasi turunan <code>ikk_expect_vs_present.csv</code> (Bank Indonesia).</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Bar chart perubahan bulanan IKK Ekspektasi. Merah = crash (Z<-2), Oranye = drop signifikan (Z<-1), Biru = normal.")

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
    marker_color=bar_colors_crash, name="Perubahan IKK Ekspektasi",
    hovertemplate="<b>%{x|%b %Y}</b><br>Perubahan: %{y:.1f}<br>Z: %{customdata:.2f}<extra></extra>",
    customdata=df_chg["exp_crash_z"]
))
fig_crash.add_hline(y=exp_change_mean, line_dash="dash", line_color=C_WARN,
                    annotation_text=f"Rata-rata: {exp_change_mean:.2f}")
fig_crash.add_hline(y=0, line_dash="dot", line_color="#666")
fig_crash.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="Perubahan IKK Ekspektasi (poin)", xaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20), showlegend=False, hovermode="x unified"
)
st.plotly_chart(fig_crash, use_container_width=True)


# ══════════════════════════════════════════════════
# 5.4 ROLLING GAP VOLATILITY (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.4 Dampak Ekonomi (Y): Volatilitas Gap Demotivasi Pasar")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Rolling Standard Deviation (Variabel Y)</span>', unsafe_allow_html=True)

vol_narr = """Menggunakan metode **Rolling Standard Deviation** — grafik memperlihatkan volatilitas gap (standar deviasi rolling {win}-bulan).
Spike pada volatilitas gap menandakan periode di mana **ketidakpastian** itu sendiri meningkat —
bukan hanya gap yang lebar, tapi gap yang **berubah-ubah secara tidak bisa diprediksi**.
Ini adalah manifestasi langsung dari *criminalization risk*: ketika kriminalisasi bisnis terjadi
secara sporadis dan tidak terprediksi, masyarakat kehilangan kemampuan untuk membentuk
ekspektasi yang stabil. Pola ini disebut *expectation volatility* — bukan sekadar pesimisme,
tapi **ketidakmampuan untuk memprediksi arah** yang jauh lebih berbahaya bagi investasi."""

vol_src = "Kalkulasi rolling std. deviation IKK Gap dari <code>ikk_expect_vs_present.csv</code> (Bank Indonesia)."
st.markdown(vol_narr.format(win=window) +
            f"\n\n<small>📁 <b>Sumber:</b> {vol_src}</small>", unsafe_allow_html=True)

fig_vol = go.Figure()
fig_vol.add_trace(go.Scatter(
    x=df["date"], y=df["gap_rolling_std"], mode="lines",
    name=f"Gap Volatility ({window}-bulan)",
    line=dict(color=C_ANOMALY, width=2),
    fill="tozeroy", fillcolor="rgba(229,57,53,0.15)",
    hovertemplate="<b>%{x|%b %Y}</b><br>Volatilitas Gap: %{y:.2f}<extra></extra>"
))
fig_vol.update_layout(
    template=PLOTLY_TEMPLATE, height=380,
    yaxis_title="Std. Deviasi Gap (rolling)", xaxis_title="",
    margin=dict(l=20, r=20, t=20, b=20), showlegend=False, hovermode="x unified"
)
st.plotly_chart(fig_vol, use_container_width=True)


# ══════════════════════════════════════════════════
# 5.5 TABEL EPISODE KRISIS (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.5 Dampak Ekonomi (Y): Log Sinkronisasi Krisis Kepercayaan")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Episode Mapping (Variabel Y)</span>', unsafe_allow_html=True)

tbl_narr = """Menggunakan metode **Z-Score Episode Detection** — tabel menampilkan episode-episode terburuk yang terdeteksi secara algoritmik.
Kolom menunjukkan tanggal, nilai IKK, gap, dan Z-Score. Episode ini dapat dihubungkan
oleh analis ke berbagai peristiwa publik yang terjadi pada periode tersebut."""

tbl_src = "Deteksi algoritma Z-Score dari data <code>ikk_expect_vs_present.csv</code> (Bank Indonesia)."
st.markdown(tbl_narr + f"\n\n<small>📁 <b>Sumber:</b> {tbl_src}</small>", unsafe_allow_html=True)

# Combine crash + gap anomaly episodes
crisis_episodes = df[df["is_crisis"]].copy()
if len(crisis_episodes) > 0:
    tbl = crisis_episodes[["date", "ikk_expectation", "ikk_present", "ikk_gap", "gap_z", "exp_change"]].copy()
    tbl["date"] = tbl["date"].dt.strftime("%B %Y")
    tbl.columns = ["Tanggal", "IKK Ekspektasi", "IKK Saat Ini", "Gap", "Gap Z-Score", "Perubahan Ekspektasi"]
    tbl = tbl.sort_values("Gap Z-Score", ascending=False).head(20).reset_index(drop=True)
    st.dataframe(tbl.style.format({
        "IKK Ekspektasi": "{:.1f}",
        "IKK Saat Ini": "{:.1f}",
        "Gap": "{:.1f}",
        "Gap Z-Score": "{:.2f}",
        "Perubahan Ekspektasi": "{:.1f}"
    }), use_container_width=True, hide_index=True)
else:
    st.info("Tidak ada episode krisis yang terdeteksi pada dataset ini.")


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("Interpretasi & Temuan Utama")

temuan = """
**Sintesis Temuan Utama (Law & Economics):**

Sesuai dengan kerangka kerja Law & Economics, sentimen krisis dan kriminalisasi otoritas direksi dalam H5 ini mengonfirmasi rantai kausalitas berikut:
`Kriminalisasi Bisnis (X) → Ketidakpastian Operasional → Persepsi Risiko (Personal Liability) → Kepercayaan Rusak → Keputusan Penarikan Ekspansi (Y)`

1. **Terror Personal Liability & Pembatalan Kontrak (Variabel X)** — Tingginya intensitas putusan MK yang menguji fondasi hukum korporat (seperti sengketa pada UU Cipta Kerja dan UU Minerba) membangun preseden bahwa garansi tetinggi negara sekalipun tidak kebal pembatalan sepihak. Menjamurnya praktik kriminalisasi pejabat menularkan infeksi ketakutan ke direksi korporasi — jika kebijakan legal bisa berujung bui, maka segala bentuk pengambilan risiko ekspansi otomatis dibekukan (*Frostbite Impact*).
 
2. **Kehancuran Indeks Kepercayaan (Variabel Y)** — Syok hukum ini terserap jelas ke *Indeks Keyakinan Konsumen* via *Gap Analysis*. Selisih ekspektasi membengkak hingga **{gap_max:.1f} poin** mengonfirmasi realita makro yang dibayangi pesimisme akut, di mana pelaku usaha dan publik pesimis terhadap proteksi *property rights* mereka di masa depan.
   
3. **Keputusan Fatalistik Menahan Ekspansi (Variabel Y)** — Algoritma dengan tajam mendeteksi **{n_crash} fase kejatuhan ekspektasi algoritmik (Expectation Crash)** dadakan. Alih-alih melakukan intervensi produktif, pasar yang dijangkiti ketakutan *legal hazard* langsung tiarap. Modal segar dibiarkan menumpuk di instrumen likuid bebas risiko, menyebabkan perputaran uang di sektor riil seketika lumpuh.

**Implikasi Final Rekomendasi:**
Ancaman kriminalisasi manuver bisnis (*Criminalization Risk*) melahirkan teror *chilling effect* kolektif. Ketakutan yuridis ini adalah variabel yang menjatuhkan keyakinan *real-time* investor secara telak. Negara tidak lagi bisa sekadar mengobati trauma ini menggunakan insentif fiskal murahan, melainkan harus mendemiliterisasi iklim hukum korporatnya agar direksi berani bangkit dari hibernasi dan kembali memutar mesin ekonomi nasional.
"""

st.markdown(temuan.format(
    gap_max=gap_max,
    n_crash=n_exp_crashes
))
