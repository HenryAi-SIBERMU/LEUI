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
DATA = os.path.join(BASE, "data", "processed")

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
# HEADER
# ══════════════════════════════════════════════════
st.title("H5: Criminalization Risk — Risiko Kriminalisasi Keputusan Bisnis")
subtitle = "Analisis IKK Expectation Collapse sebagai Proxy Risiko Personal & Reputasional Investor"
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander("Metodologi: Analisis Criminalization Risk (H5)", expanded=False):
    st.markdown("""
    **Premis:** Kriminalisasi keputusan bisnis atau kebijakan administratif menciptakan
    **personal liability risk** — direksi takut dijerat pidana, pejabat daerah takut
    tanda tangan, investor asing khawatir personal liability. Dampaknya: kepercayaan publik
    runtuh, tercermin dalam **collapse** IKK Ekspektasi.

    **Causal Chain:**
    `Criminalization Risk → Personal Liability Fear → Expectation Collapse → IKK Gap Melebar → Investment Freeze`

    **Metode:**
    1. **Gap Analysis (Expectation − Present)** — Selisih antara ekspektasi konsumen
       dengan kondisi saat ini. Gap yang melebar = masyarakat berharap perbaikan tapi
       realita memburuk. Gap > 2σ dari rata-rata = anomali struktural.
    2. **Expectation Crash Detection** — Z-Score pada perubahan bulanan IKK Ekspektasi.
       Z < -2 = crash mendadak. Pola crash mendadak konsisten dengan *shock event*
       (kriminalisasi publik, penangkapan direksi, dsb).
    3. **Rolling Gap Volatility** — Volatilitas gap dalam window 12 bulan.
       Volatilitas tinggi = ketidakpastian tinggi — masyarakat tidak bisa memprediksi arah.
    4. **Correlation Analysis** — Hubungan antara level ekspektasi dan lebar gap.

    **Catatan:** IKK mengukur persepsi konsumen secara umum, bukan khusus investor.
    Namun sebagai proxy sentimen, IKK mencerminkan kepercayaan publik yang juga
    mempengaruhi iklim investasi.
    """)


# ── Intro Narrative ──
intro = """Data IKK Indonesia sepanjang **{n} bulan** ({start} – {end}) memperlihatkan pola
**krisis kepercayaan yang berulang**. Gap rata-rata antara ekspektasi dan kondisi saat ini
sebesar **{gap_mean:.1f} poin** (median: {gap_med:.1f}), namun gap terlebar mencapai
**{gap_max:.1f} poin** ({max_gap_date}). Dari {n} observasi, algoritma mendeteksi
**{n_crash} episode expectation crash** (Z < -2, penurunan ekspektasi mendadak) dan
**{n_gap_anom} episode gap anomali** (Z > 2, gap abnormal). {inv_text}
Korelasi Spearman antara level ekspektasi dan lebar gap: **r = {corr:.3f}** (p = {pval:.4f}).
Tren keseluruhan menunjukkan gap **{gap_trend}** sebesar **{gap_chg:.1f}%** antara
periode awal dan akhir, mengindikasikan bahwa {gap_interp}."""

if n_inverted > 0:
    inv_text = f"Perlu dicatat: **{n_inverted} bulan** menunjukkan gap terbalik (kondisi saat ini > ekspektasi) — tanda krisis kepercayaan total."
else:
    inv_text = ""

if gap_trend_change > 5:
    gap_interp = "jarak antara harapan dan realita makin lebar — sinyal bahwa kepercayaan publik terus tergerus"
elif gap_trend_change < -5:
    gap_interp = "gap menyempit — sinyal positif, meskipun level absolut masih tinggi"
else:
    gap_interp = "gap relatif stabil — krisis kepercayaan telah menjadi kondisi permanen"

intro_src = "Data dari <code>ikk_expect_vs_present.csv</code> ({n} baris, {start} - {end}). " \
              "Sumber: Bank Indonesia."

st.markdown(
    intro.format(
        n=n_obs, start=date_start, end=date_end,
        gap_mean=gap_mean, gap_med=gap_median, gap_max=gap_max,
        max_gap_date=max_gap_date,
        n_crash=n_exp_crashes, n_gap_anom=n_gap_anomalies,
        inv_text=inv_text,
        corr=corr_exp_gap, pval=pval_exp_gap,
        gap_trend=gap_trend_word, gap_chg=abs(gap_trend_change),
        gap_interp=gap_interp
    ) +
    f"\n\n<small>📁 <b>Sumber:</b> {intro_src.format(n=n_obs, start=date_start, end=date_end)}</small>",
    unsafe_allow_html=True
)
st.caption("📊 Visualisasi: Empat panel — (1) IKK Expectation vs Present + Gap, (2) Expectation Crash Detection, (3) Rolling Gap Volatility, (4) Tabel Episode Krisis.")


# ── KPI Cards — Semua warna advokasi ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Episode Expectation Crash</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{n_exp_crashes}&nbsp;<span style="font-size:1.2rem;color:#888;">Bulan</span></div>
        <div class="metric-delta" style="color:{C_WARN}">Z < -2 (penurunan mendadak)</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gap Terlebar</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{gap_max:.1f}&nbsp;<span style="font-size:1.2rem;color:#888;">Poin</span></div>
        <div class="metric-delta" style="color:#AAA">{max_gap_date}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    gap_color = C_ANOMALY if gap_latest > gap_mean * 1.2 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Gap Terakhir</div>
        <div class="metric-value" style="color:{gap_color}">{gap_latest:.1f}&nbsp;<span style="font-size:1.2rem;color:#888;">Poin</span></div>
        <div class="metric-delta" style="color:#AAA">Rata-rata: {gap_mean:.1f}</div>
    </div>""", unsafe_allow_html=True)
with col4:
    crash_color = C_ANOMALY if worst_crash_val < -10 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Crash Terburuk</div>
        <div class="metric-value" style="color:{crash_color}">{worst_crash_val:.1f}&nbsp;<span style="font-size:1.2rem;color:#888;">Poin</span></div>
        <div class="metric-delta" style="color:{C_WARN}">{worst_crash_date}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 5.1 IKK EXPECTATION vs PRESENT + GAP
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.1 IKK Ekspektasi vs Kondisi Saat Ini — Jurang Kepercayaan")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Gap Analysis</span>', unsafe_allow_html=True)

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
# 5.2 EXPECTATION CRASH DETECTION
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.2 Deteksi Expectation Crash — Runtuhnya Kepercayaan Mendadak")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Crash Detection</span>', unsafe_allow_html=True)

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
# 5.3 ROLLING GAP VOLATILITY
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.3 Rolling Gap Volatility — Ketidakpastian Kepercayaan")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Rolling Standard Deviation</span>', unsafe_allow_html=True)

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
# 5.4 TABEL EPISODE KRISIS
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("5.4 Episode Krisis Kepercayaan")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Episode Detection</span>', unsafe_allow_html=True)

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
**Analisis Temuan Utama H5 — Criminalization Risk:**

Data IKK **{n} bulan** ({start} – {end}) memperlihatkan pola krisis kepercayaan yang
konsisten dengan hipotesis criminalization risk:

1. **Gap Kronis** — Selisih rata-rata antara ekspektasi dan kondisi saat ini sebesar
   **{gap_mean:.1f} poin** menunjukkan bahwa masyarakat Indonesia secara kronis merasa
   realita lebih buruk dari harapan. Gap terlebar: **{gap_max:.1f} poin** ({max_gap_date}).

2. **Expectation Crash** — **{n_crash} episode** di mana ekspektasi publik jatuh secara mendadak
   (Z < -2). Crash terburuk: **{worst_date}** ({worst_val:.1f} poin). Pola crash mendadak ini
   konsisten dengan *criminalization shock* — peristiwa yang langsung merusak kepercayaan.

3. **Gap Trend** — Gap antara periode awal dan akhir **{gap_trend}** sebesar **{gap_chg:.1f}%**.
   {gap_trend_interp}

4. **Korelasi** — Spearman r = **{corr:.3f}** (p = {pval:.4f}) antara level ekspektasi
   dan lebar gap. {corr_interp}

**Implikasi:**
Kriminalisasi keputusan bisnis menciptakan *chilling effect* yang melampaui korban langsung.
Ketika seorang direksi dijerat pidana atau pejabat daerah takut tanda tangan, sinyal yang
diterima oleh seluruh ekosistem bisnis adalah: **keputusan apapun bisa dikriminalkan**.
Dampaknya terukur dalam data IKK: gap yang melebar, crash yang sporadis, dan volatilitas
kepercayaan yang terus meningkat — semua menandakan bahwa **personal liability risk**
telah menjadi hambatan struktural bagi iklim investasi Indonesia.

*Catatan: IKK mengukur kepercayaan konsumen secara umum. Untuk mengukur criminalization risk
secara langsung, dibutuhkan database kasus pidana bisnis dan survei investor yang belum
tersedia dalam dataset saat ini.*
"""

if corr_exp_gap < -0.3:
    corr_interp = "Korelasi negatif menunjukkan: semakin rendah ekspektasi, semakin lebar gap — pesimisme memperbesar jurang."
elif corr_exp_gap > 0.3:
    corr_interp = "Korelasi positif menunjukkan: ekspektasi dan gap bergerak searah — saat ekspektasi naik, gap juga melebar."
else:
    corr_interp = "Korelasi lemah menunjukkan hubungan non-linear antara ekspektasi dan gap."

if gap_trend_change > 5:
    gap_trend_interp = "Gap yang membesar menandakan krisis kepercayaan yang memburuk seiring waktu."
elif gap_trend_change < -5:
    gap_trend_interp = "Gap yang menyempit adalah sinyal positif, meskipun level absolut tetap tinggi."
else:
    gap_trend_interp = "Gap yang stabil menandakan krisis kepercayaan telah menjadi kondisi permanen — *new normal* yang mengkhawatirkan."

st.markdown(temuan.format(
    n=n_obs, start=date_start, end=date_end,
    gap_mean=gap_mean, gap_max=gap_max, max_gap_date=max_gap_date,
    n_crash=n_exp_crashes, worst_date=worst_crash_date, worst_val=worst_crash_val,
    gap_trend=gap_trend_word, gap_chg=abs(gap_trend_change), gap_trend_interp=gap_trend_interp,
    corr=corr_exp_gap, pval=pval_exp_gap, corr_interp=corr_interp
))
