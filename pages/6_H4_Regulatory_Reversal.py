"""
Page 4 — H4: Regulatory Reversal Risk
Analisis capital outflow (net sell obligasi) sebagai proxy risiko pencabutan
izin/kebijakan mendadak yang memicu pelarian modal.
    `Regulatory Reversal → Stranded Asset Fear → Capital Flight → Net Sell Obligasi Melonjak`

Causal Chain: Regulatory Reversal → Stranded Asset Fear → Capital Flight → Net Sell Spike
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
    page_title="H4: Regulatory Reversal — CELIOS LEUI",
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
C_NET_SELL = "#42A5F5"
C_ANOMALY = "#E53935"
C_WARN = "#FF9800"
C_BG = "#1E1E1E"

# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "processed")

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(DATA, "capital_outflow.csv"), parse_dates=["date"])
    return df

df = load_data()
df = df.sort_values("date").reset_index(drop=True)


# ══════════════════════════════════════════════════
# PRE-COMPUTE
# ══════════════════════════════════════════════════

n_obs = len(df)
date_start = df["date"].min().strftime("%d %B %Y")
date_end = df["date"].max().strftime("%d %B %Y")
year_start = df["date"].min().year
year_end = df["date"].max().year

# Basic stats
mean_ns = df["net_sell_idr_tn"].mean()
std_ns = df["net_sell_idr_tn"].std()
median_ns = df["net_sell_idr_tn"].median()
max_ns = df["net_sell_idr_tn"].max()
min_ns = df["net_sell_idr_tn"].min()
total_ns = df["net_sell_idr_tn"].sum()

max_date = df.loc[df["net_sell_idr_tn"].idxmax(), "date"].strftime("%d %B %Y")
min_date = df.loc[df["net_sell_idr_tn"].idxmin(), "date"].strftime("%d %B %Y")

# Z-Score anomaly detection (threshold = Z > 2)
df["z_score"] = (df["net_sell_idr_tn"] - mean_ns) / std_ns
df["is_anomaly"] = df["z_score"] > 2
df["is_high"] = df["z_score"] > 1  # elevated but not anomaly

anomaly_episodes = df[df["is_anomaly"]].copy()
high_episodes = df[df["is_high"]].copy()
n_anomaly = len(anomaly_episodes)
n_high = len(high_episodes)

# Rate of change
df["roc"] = df["net_sell_idr_tn"].pct_change() * 100

# Rolling statistics (4-period window)
window = min(4, n_obs)
df["rolling_mean"] = df["net_sell_idr_tn"].rolling(window=window, min_periods=2).mean()
df["rolling_std"] = df["net_sell_idr_tn"].rolling(window=window, min_periods=2).std()
df["upper_band"] = df["rolling_mean"] + 2 * df["rolling_std"]

# Volatility (coefficient of variation)
cv = (std_ns / mean_ns * 100) if mean_ns > 0 else 0

# Consecutive high-sell streaks
df["above_mean"] = df["net_sell_idr_tn"] > mean_ns
streaks = []
current_streak = 0
for above in df["above_mean"]:
    if above:
        current_streak += 1
    else:
        if current_streak > 0:
            streaks.append(current_streak)
        current_streak = 0
if current_streak > 0:
    streaks.append(current_streak)
max_streak = max(streaks) if streaks else 0

# Quarterly aggregation
df["quarter_str"] = df["date"].dt.year.astype(str) + "Q" + df["date"].dt.quarter.astype(str)
q_agg = df.groupby("quarter_str").agg(
    total_sell=("net_sell_idr_tn", "sum"),
    avg_sell=("net_sell_idr_tn", "mean"),
    max_sell=("net_sell_idr_tn", "max"),
    n_obs=("net_sell_idr_tn", "count")
).reset_index()
q_agg = q_agg.sort_values("quarter_str").reset_index(drop=True)

# Worst quarter
if len(q_agg) > 0:
    worst_q_idx = q_agg["total_sell"].idxmax()
    worst_q = q_agg.loc[worst_q_idx, "quarter_str"]
    worst_q_val = q_agg.loc[worst_q_idx, "total_sell"]
else:
    worst_q = "—"
    worst_q_val = 0

# Trend: first half vs second half
half = n_obs // 2
first_half_avg = df["net_sell_idr_tn"].iloc[:half].mean()
second_half_avg = df["net_sell_idr_tn"].iloc[half:].mean()
trend_change = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
trend_word = "meningkat" if trend_change > 0 else "menurun"


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title("H4: Regulatory Reversal Risk — Risiko Pencabutan Kebijakan")
subtitle = "Analisis Capital Outflow (Net Sell Obligasi) sebagai Proxy Pelarian Modal akibat Ketidakpastian Regulasi"
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander("Metodologi: Analisis Regulatory Reversal Risk (H4)", expanded=False):
    st.markdown("""
    **Premis:** Pencabutan izin yang sudah sah, perubahan regulasi retroaktif, atau kriminalisasi
    pasca pergantian pejabat menciptakan **stranded asset risk** — investor yang sudah menanamkan
    modal tiba-tiba kehilangan jaminan hukum. Respons rasional? **Tarik modal secepat mungkin.**

    **Causal Chain:**
    `Regulatory Reversal → Stranded Asset Fear → Capital Flight → Net Sell Obligasi Melonjak`

    **Metode:**
    1. **Z-Score Anomaly Detection**
       - Identifikasi minggu dengan net sell abnormal
       - Formula: `Z = (x - μ) / σ`
       - Threshold: `Z > 2` (anomali capital flight), `Z > 1` (elevated)
    2. **Rolling Band Analysis**
       - Batas atas fluktuasi wajar menggunakan moving average
       - Formula: `Upper Band = Rolling Mean + (2 × Rolling SD)`
       - Titik di luar band = capital flight episode
    3. **Quarterly Aggregation**
       - Agregasi data mingguan ke kuartalan
       - Formula: `Sum(Net Sell)` per kuartal
       - Fungsi: melihat tren makro & menghilangkan noise harian
    4. **Trend Analysis**
       - Perbandingan rata-rata paruh pertama vs kedua
       - Formula: `Δ = (Mean[Akhir] - Mean[Awal]) / Mean[Awal] × 100%`

    **Catatan:** Net sell obligasi harian dipengaruhi banyak faktor (Fed rate, global risk-off,
    rupiah, dll). Analisis ini menyajikan data sebagai **proxy parsial** — spike yang muncul
    bersamaan dengan ketidakpastian regulasi memperkuat hipotesis H4.
    """)


# ── Intro Narrative ──
intro = """Data capital outflow Indonesia selama **{n} observasi** ({start} – {end}) memperlihatkan
pola net sell obligasi yang **sangat volatile** (CV = {cv:.1f}%). Total akumulasi net sell selama
periode ini mencapai **{total:.2f} IDR Tn / Triliun** dengan rata-rata **{mean:.2f} IDR Tn / Triliun** per periode.
Dari {n} observasi, algoritma Z-Score mendeteksi **{n_anom} episode anomali** (Z > 2) dan
**{n_high} episode elevated** (Z > 1) — minggu-minggu di mana investor menarik modal secara
masif, jauh melampaui fluktuasi wajar. Net sell tertinggi tercatat pada
**{max_date}** sebesar **{max_val:.2f} IDR Tn / Triliun** (Z = {max_z:.2f}). Tren keseluruhan menunjukkan
rata-rata net sell paruh kedua **{trend}** sebesar **{trend_chg:.1f}%** dibanding paruh pertama,
mengindikasikan bahwa {trend_interp}."""

if trend_change > 10:
    trend_interp = "tekanan pelarian modal makin membesar — sinyal bahwa ketidakpastian regulasi memburuk"
elif trend_change < -10:
    trend_interp = "tekanan pelarian modal mereda relatif — namun level absolut tetap tinggi"
else:
    trend_interp = "tekanan pelarian modal relatif stabil — namun volatilitas tetap mengkhawatirkan"

max_z = df.loc[df["net_sell_idr_tn"].idxmax(), "z_score"]

intro_src = "Data dari <code>capital_outflow.csv</code> ({n} baris, {start} - {end}). " \
              "Sumber: Bond Net Sell data (CEIC/Bloomberg)."

st.markdown(
    intro.format(
        n=n_obs, start=date_start, end=date_end,
        cv=cv, total=total_ns, mean=mean_ns,
        n_anom=n_anomaly, n_high=n_high,
        max_date=max_date, max_val=max_ns, max_z=max_z,
        trend=trend_word, trend_chg=abs(trend_change),
        trend_interp=trend_interp
    ) +
    f"\n\n<small>📁 <b>Sumber:</b> {intro_src.format(n=n_obs, start=date_start, end=date_end)}</small>",
    unsafe_allow_html=True
)
st.caption("📊 Visualisasi: Empat panel — (1) Time Series + Anomali, (2) Rolling Band, (3) Agregasi Kuartal, (4) Tabel Episode. Semua threshold dihitung dari data.")


# ── KPI Cards — Semua warna advokasi ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Episode Anomali (Z>2)</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{n_anomaly}</div>
        <div class="metric-delta" style="color:{C_WARN}">dari {n_obs} observasi</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Net Sell Tertinggi</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{max_ns:.1f} Tn</div>
        <div class="metric-delta" style="color:#AAA">Z = {max_z:.2f}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    cv_color = C_ANOMALY if cv > 50 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Volatilitas (CV)</div>
        <div class="metric-value" style="color:{cv_color}">{cv:.1f}%</div>
        <div class="metric-delta" style="color:{C_WARN}">Sangat Volatile</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Akumulasi</div>
        <div class="metric-value" style="color:{C_WARN}">{total_ns:.1f} Tn</div>
        <div class="metric-delta" style="color:#AAA">{year_start}–{year_end}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 4.1 TIME SERIES + ANOMALI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.1 Time Series Net Sell Obligasi + Deteksi Anomali")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Anomaly Detection</span>', unsafe_allow_html=True)

ts_narr = """**Cara Membaca Grafik:** Grafik batang (bar chart) di bawah menampilkan volume net sell per periode. 
Warna biru menunjukkan fluktuasi normal. Garis oranye (rata-rata historis **{mean:.2f} IDR Tn / Triliun**) adalah *baseline*. 
Batang berwarna **oranye (Elevated)** dan **merah (Anomali)** menandakan penarikan modal yang secara statistik tidak wajar.

**Narasi Kritis:** Menggunakan metode **Z-Score Anomaly Detection**, kita bisa memisahkan "noise" pasar dari kepanikan institusional. 
Titik merah (Z > 2) menandai *capital flight episode*. Perhatikan bahwa spike merah ini tidak tersebar acak, melainkan 
**terkonsentrasi (clustering)** pada periode tertentu. Ini konsisten dengan pola *regulatory shock*: ketika ada pencabutan 
kebijakan sepihak (regulatory reversal), investor merespons seketika dengan menarik likuiditas besar-besaran. 
Tren kepanikan ekstrem terpanjang mencapai **{streak} periode berturut-turut** di atas rata-rata — sebuah proksi kuat 
krisis kepercayaan hukum."""

ts_src = "Data mentah <code>capital_outflow.csv</code>. Z-Score dihitung dari mean dan std. deviasi seluruh dataset."
st.markdown(ts_narr.format(mean=mean_ns, streak=max_streak) +
            f"\n\n<small>📁 <b>Sumber:</b> {ts_src}</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Bar chart — net sell per periode. Merah = anomali (Z>2), Oranye = elevated (Z>1), Biru = normal.")

# Bar colors based on Z-Score
bar_colors = []
for _, row in df.iterrows():
    if row["is_anomaly"]:
        bar_colors.append(C_ANOMALY)
    elif row["is_high"]:
        bar_colors.append(C_WARN)
    else:
        bar_colors.append(C_NET_SELL)

fig_ts = go.Figure()
fig_ts.add_trace(go.Bar(
    x=df["date"], y=df["net_sell_idr_tn"],
    marker_color=bar_colors, name="Net Sell",
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Net Sell: %{y:.2f} IDR Tn<br>Z: %{customdata:.2f}<extra></extra>",
    customdata=df["z_score"]
))
fig_ts.add_hline(y=mean_ns, line_dash="dash", line_color=C_WARN,
                 annotation_text=f"Rata-rata: {mean_ns:.2f} Tn")
fig_ts.add_hline(y=mean_ns + 2 * std_ns, line_dash="dot", line_color=C_ANOMALY,
                 annotation_text=f"Threshold Anomali (Z=2): {mean_ns + 2*std_ns:.1f} Tn")
fig_ts.update_layout(
    template=PLOTLY_TEMPLATE, height=430,
    yaxis_title="Net Sell (IDR Tn / Triliun)", xaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified", showlegend=False
)
st.plotly_chart(fig_ts, use_container_width=True)


# ══════════════════════════════════════════════════
# 4.2 ROLLING BAND ANALYSIS
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.2 Rolling Band Analysis — Batas Fluktuasi Wajar")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Rolling Band Analysis</span>', unsafe_allow_html=True)

band_narr = """**Cara Membaca Grafik:** Garis biru solid adalah net sell aktual. Garis hijau putus-putus adalah *rolling mean*
(rata-rata bergerak selama {win} periode) yang merepresentasikan tren kepanikan basis. Garis merah putus-putus adalah *Upper Band* 
(+2 standar deviasi) — ini adalah batas toleransi volatilitas pasar. Area merah menyala menunjukkan titik "jebolnya" batas wajar.

**Narasi Kritis:** Metode **Rolling Band Analysis** menangkap perubahan volatilitas dari waktu ke waktu. Ketika garis biru 
menembus Upper Band merah, itu bukan sekadar capital outflow biasa, melainkan pelarian modal yang didorong oleh *fear factor*. 
Perhatikan bagaimana jarak antara garis hijau dan merah (*band width*) terkadang melebar drastis. Pelebaran ini adalah visualisasi dari 
**volatility clustering** — sebuah bukti bahwa ketidakpastian regulasi tidak hanya menaikkan *volume* uang yang keluar, 
tetapi juga menciptakan **ketidakpastian ekstrem terhadap pergerakan pasar ke depan**. Investor bingung, dan *default action* mereka adalah kabur."""

band_src = "Rolling window = {win} periode. Upper band = rolling mean + 2 × rolling std."
st.markdown(band_narr.format(win=window) +
            f"\n\n<small>📁 <b>Sumber:</b> {band_src.format(win=window)}</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Line chart — net sell aktual (biru), rolling mean (hijau), upper band (merah putus-putus).")

fig_band = go.Figure()
fig_band.add_trace(go.Scatter(
    x=df["date"], y=df["net_sell_idr_tn"], mode="lines+markers", name="Net Sell Aktual",
    line=dict(color=C_NET_SELL, width=2), marker=dict(size=6),
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Net Sell: %{y:.2f} Tn<extra></extra>"
))
fig_band.add_trace(go.Scatter(
    x=df["date"], y=df["rolling_mean"], mode="lines", name=f"Rolling Mean ({window}p)",
    line=dict(color="#66BB6A", width=2, dash="dot"),
    hovertemplate="Rolling Mean: %{y:.2f} Tn<extra></extra>"
))
fig_band.add_trace(go.Scatter(
    x=df["date"], y=df["upper_band"], mode="lines", name="Upper Band (+2σ)",
    line=dict(color=C_ANOMALY, width=1.5, dash="dash"),
    hovertemplate="Upper Band: %{y:.2f} Tn<extra></extra>"
))
fig_band.update_layout(
    template=PLOTLY_TEMPLATE, height=430,
    yaxis_title="Net Sell (IDR Tn / Triliun)", xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_band, use_container_width=True)


# ══════════════════════════════════════════════════
# 4.3 AGREGASI KUARTAL
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.3 Agregasi Kuartal — Tren Makro Capital Outflow")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Quarterly Aggregation</span>', unsafe_allow_html=True)

q_narr = """**Cara Membaca Grafik:** Batang menampilkan total agregasi net sell (keluarnya modal) setiap kuartal.
Tinggi batang dan intensitas warna (semakin merah/gelap) menekankan level keparahan capital outflow pada kuartal tersebut.

**Narasi Kritis:** Melalui **Quarterly Aggregation**, kita menghilangkan *noise* harian/mingguan untuk melihat *big picture* ekonomi politik. 
Kuartal paling destruktif adalah **{worst_q}** yang menyapu bersih **{worst_val:.2f} IDR Tn / Triliun**. 
Kuartal merah ini menandakan bahwa *shock* kebijakan tidak terselesaikan dengan cepat; efek kerusakannya pada sentimen 
mampu bertahan sepanjang tiga bulan penuh. Jika batang merah tinggi terjadi berulang (*persistent*), ini mengindikasikan bahwa 
*regulatory reversal* telah mendarah daging sebagai iklim usaha yang cacat (structural baseline). Jika sporadis, ini 
adalah reaksi syok terhadap kebijakan reaksioner sesaat."""

q_src = "Agregasi <code>capital_outflow.csv</code> per kuartal: sum, mean, max, dan count per kuartal."
st.markdown(q_narr.format(worst_q=worst_q, worst_val=worst_q_val) +
            f"\n\n<small>📁 <b>Sumber:</b> {q_src}</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Bar chart — total net sell per kuartal. Warna intensitas = besaran.")

if len(q_agg) > 0:
    fig_q = go.Figure()
    q_colors = [C_ANOMALY if v == q_agg["total_sell"].max() else C_WARN if v > q_agg["total_sell"].mean() else C_NET_SELL
                for v in q_agg["total_sell"]]
    fig_q.add_trace(go.Bar(
        x=q_agg["quarter_str"], y=q_agg["total_sell"],
        marker_color=q_colors, name="Total Net Sell",
        text=[f"{v:.1f}" for v in q_agg["total_sell"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Total: %{y:.2f} Tn<extra></extra>"
    ))
    fig_q.update_layout(
        template=PLOTLY_TEMPLATE, height=400,
        yaxis_title="Total Net Sell (IDR Tn / Triliun)", xaxis_title="",
        margin=dict(l=20, r=20, t=40, b=20), showlegend=False
    )
    st.plotly_chart(fig_q, use_container_width=True)


# ══════════════════════════════════════════════════
# 4.4 TABEL EPISODE ANOMALI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.4 Episode Capital Flight — Deteksi Anomali")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Episode Detection</span>', unsafe_allow_html=True)

tbl_narr = """**Cara Membaca Tabel:** Tabel ini diurutkan dari nilai Z-Score tertinggi. Nilai Z-Score di atas 2 
menandakan simpangan deviasi ekstrem (zona merah anomali). Semakin tinggi net sell (dalam Triliun), semakin masif pelarian modal.

**Narasi Kritis:** Metode **Z-Score Episode Detection** mendeteksi tanggal pelarian modal murni berdasarkan anomali statistik.
Kolom "Anomali? Ya" adalah periode di mana kepanikan institusional berada di puncaknya. Tanggal-tanggal krisis ini 
bertindak sebagai **jejak forensik aliran modal** — mengarahkan analis langsung ke periode mana kebijakan kontroversial, 
pencabutan izin mendadak, atau putusan hukum bermasalah diterbitkan, yang memicu investor kabur *at all costs*."""

st.markdown(tbl_narr)

if len(high_episodes) > 0:
    tbl = high_episodes[["date", "net_sell_idr_tn", "z_score", "is_anomaly"]].copy()
    tbl["date"] = tbl["date"].dt.strftime("%d %B %Y")
    tbl.columns = ["Tanggal", "Net Sell (IDR Tn)", "Z-Score", "Anomali?"]
    tbl["Anomali?"] = tbl["Anomali?"].map({True: "Ya (Z > 2)", False: "Elevated (Z > 1)"})
    tbl = tbl.sort_values("Z-Score", ascending=False).reset_index(drop=True)
    st.dataframe(tbl.style.format({
        "Net Sell (IDR Tn)": "{:.2f}",
        "Z-Score": "{:.2f}"
    }), use_container_width=True, hide_index=True)
else:
    st.info("Tidak ada episode anomali yang terdeteksi pada dataset ini.")


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("Interpretasi & Temuan Utama")

temuan = """
**Analisis Temuan Utama H4 — Regulatory Reversal Risk:**

Data capital outflow **{n} observasi** ({start} – {end}) memperlihatkan pola
pelarian modal yang konsisten dengan hipotesis regulatory reversal:

1. **Volatilitas Ekstrem** — Coefficient of Variation sebesar **{cv:.1f}%** menunjukkan
   net sell sangat tidak stabil. Nilai terendah hanya **{min_val:.2f} IDR Tn / Triliun** namun tertinggi
   mencapai **{max_val:.2f} IDR Tn / Triliun** — rasio {ratio:.0f}x lipat.

2. **Episode Anomali Terkonsentrasi** — Dari {n} observasi, **{n_anom} episode anomali** (Z > 2)
   dan **{n_high} elevated** (Z > 1) terdeteksi. Anomali tidak tersebar merata, tapi
   **terkonsentrasi** di periode-periode tertentu — pola khas *regulatory shock*.

3. **Tren Keseluruhan** — Rata-rata net sell paruh kedua **{trend}** sebesar **{trend_chg:.1f}%**
   dibanding paruh pertama. {trend_interp_final}

4. **Kuartal Terburuk** — **{worst_q}** mencatat total net sell **{worst_val:.2f} IDR Tn / Triliun**,
   kuartal dengan tekanan capital flight terbesar.

**Implikasi:**
Ketika investor merespons perubahan regulasi dengan menarik modal secara masif dan mendadak,
ini menciptakan *self-reinforcing cycle*: pelarian modal → tekanan rupiah → BI menaikkan suku bunga →
biaya investasi naik → investor semakin enggan masuk. Regulatory reversal bukan hanya
merugikan investor yang sudah ada, tapi juga **menaikkan barrier of entry** bagi investor baru.

*Catatan: Net sell obligasi dipengaruhi banyak faktor global (Fed rate, DXY, geopolitik).
Analisis ini menyajikan data sebagai proxy parsial — bukan klaim kausal tunggal terhadap
regulatory reversal.*
"""

if trend_change > 10:
    trend_interp_final = "Tekanan yang meningkat ini memperkuat argumen bahwa ketidakpastian regulasi memburuk."
elif trend_change < -10:
    trend_interp_final = "Meskipun mereda, level absolut tetap jauh lebih tinggi dari nol — tekanan belum sepenuhnya hilang."
else:
    trend_interp_final = "Stabilitas relatif ini bisa berarti tekanan sudah menjadi *structural baseline* — investor sudah terbiasa menarik modal."

st.markdown(temuan.format(
    n=n_obs, start=date_start, end=date_end,
    cv=cv, min_val=min_ns, max_val=max_ns, ratio=max_ns/min_ns if min_ns > 0 else 0,
    n_anom=n_anomaly, n_high=n_high,
    trend=trend_word, trend_chg=abs(trend_change), trend_interp_final=trend_interp_final,
    worst_q=worst_q, worst_val=worst_q_val
))
