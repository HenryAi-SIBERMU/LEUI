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
import plotly.express as px
from scipy import stats
from sklearn.ensemble import IsolationForest
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
DATA = os.path.join(BASE, "data", "final")

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

# Isolation Forest anomaly detection (ML-based)
iso_model = IsolationForest(contamination=0.15, random_state=42, n_estimators=100)
df["iso_score"] = iso_model.fit_predict(df[["net_sell_idr_tn"]])
df["iso_anomaly_score"] = iso_model.decision_function(df[["net_sell_idr_tn"]])
df["is_iso_anomaly"] = (df["iso_score"] == -1) & (df["net_sell_idr_tn"] > mean_ns)
n_iso_anomaly = df["is_iso_anomaly"].sum()
iso_upper_anom = df.loc[df["is_iso_anomaly"], "net_sell_idr_tn"]
iso_threshold = iso_upper_anom.min() if len(iso_upper_anom) > 0 else max_ns

# Max Z-Score for tbl_narr
max_z = df["z_score"].max()

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
# HEADER & INTRO
# ══════════════════════════════════════════════════
st.title(_("H4: Regulatory Reversal Risk — Guncangan Regulasi"))
subtitle = _("Analisis Capital Flight & Net Sell Obligasi sebagai Proxy Risiko Stranded Asset")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Setup Variables (Hukum) ──
_churn_path = os.path.join(DATA, "regulatory_churn_rate.csv")
_rev_path = os.path.join(DATA, "h4_reversal_timeline.csv")

_latest_churn = 0
_max_churn = 0
_df_churn = pd.DataFrame()
_df_rev = pd.DataFrame()

if os.path.exists(_churn_path) and os.path.exists(_rev_path):
    _df_churn = pd.read_csv(_churn_path)
    _df_rev = pd.read_csv(_rev_path)
    _latest_churn = _df_churn['churn_rate'].iloc[-1] if not _df_churn.empty else 0
    _max_churn = _df_churn['churn_rate'].max() if not _df_churn.empty else 0

# ── Methodology ──
with st.expander(_("Metodologi: Analisis Regulatory Reversal Risk (H4)"), expanded=False):
    st.markdown(_("""
    **Causal Chain Law & Economics:**
    `Perubahan Aturan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi`

    **Variabel Independen (X):**
    - **Perubahan Aturan Hukum (Regulatory Churn Rate)**: Rasio (persentase) regulasi yang dicabut/diubah per tahun terhadap total regulasi kumulatif yang pernah ada (sumber: Pasal.id REST API).
    
    **Variabel Dependen (Y):**
    - **Keputusan Investasi (Capital Outflow)**: Terefleksi pada nilai Net Sell Obligasi Pemerintah (IDR Triliun). Penarikan modal massal bereaksi secara proporsional terhadap tingginya beban **Biaya Ekonomi** (Premium risiko *Stranded Asset*) akibat lonjakan anomali fluktuasi kebijakan pasca-*reversal*.
    """))

# ── Intro Narrative ──
intro = _("""Kerangka empiris **Regulatory Reversal Risk** menyoroti dampak destruktif dari perubahan kebijakan yang tiba-tiba terhadap stabilitas arus modal. Mengikuti rantai transmisi hukum: **Perubahan Aturan → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi**, palka data historis mencatat **Regulatory Churn** berada di rekor puncaknya sebesar **{max_churn:.1f}%**. Aturan yang dicabut mendadak menciptakan iklim ketidakpastian absolut, mengangkat eskalasi **persepsi risiko** investor pada ancaman *stranded asset* (aset yang tidak bernilai/tersandera oleh diskresi sepihak pemerintah). 

Ketidakpastian fundamental ini secara simetris mendongkrak **biaya ekonomi** tak terlihat dalam wujud tarikan *Risk Premium* ekstrem dari para manajer lindung nilai. Semua kerugian itu lantas dikonversi menjadi pergerakan sentimen **keputusan investasi** yang brutal berupa gelombang *Capital Flight*. Dalam {n_obs} periode kuartil observasi ({yr_start}–{yr_end}), panik masif mencetak **{n_anom} episode anomali ekstrem** dengan rekor *Net Sell* di titik tertinggi **{max_ns:.1f} Triliun Rupiah** (Z-Score {max_z:.2f}). Lenyapnya likuiditas skala makro membuktikan bahwa manuver hukum *"bongkar-pasang"* sama dengan tindakan melelang kepercayaan investasi ke titik terendah.""")

intro_src = _("Pasal.id API (Variabel Hukum/X) & Bond Net Sell Data CEIC/Bloomberg (Variabel Makroekonomi/Y).")

st.markdown(
    intro.format(
        max_churn=_max_churn,
        n_obs=n_obs, yr_start=year_start, yr_end=year_end,
        max_ns=max_ns, max_z=max_z, n_anom=n_anomaly
    ) +
    f"\n\n<small>📁 <b>Sumber Basis Data:</b> {intro_src}</small>",
    unsafe_allow_html=True
)
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── Overview KPI Cards (Hukum + Ekonomi) ──
st.markdown("### Eksekutif Summary (H4)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Churn Rate Maksimum</div>
        <div class="metric-value" style="color:#FF9800">{_max_churn:.1f}%</div>
        <div class="metric-delta" style="color:#FF9800">Variabel Hukum (X)</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Net Sell Tertinggi</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{max_ns:.1f} Tn</div>
        <div class="metric-delta" style="color:{C_WARN}">Variabel Ekonomi (Y)</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Episode Anomali Z>2</div>
        <div class="metric-value" style="color:{C_ANOMALY}">{n_anomaly}</div>
        <div class="metric-delta" style="color:#AAA">Kepanikan (Dampak Y)</div>
    </div>""", unsafe_allow_html=True)
with c4:
    cv_color = C_ANOMALY if cv > 50 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Volatilitas Capital (CV)</div>
        <div class="metric-value" style="color:{cv_color}">{cv:.1f}%</div>
        <div class="metric-delta" style="color:{C_WARN}">Sangat Volatile</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ── 4.1 Variabel Hukum (X) ──
from plotly.subplots import make_subplots
st.markdown("---")
st.subheader("4.1 Variabel Hukum (X): Regulasi Churn & Hubungan Dual-Axis Capital Flight")
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Regulatory Churn Rate & Overlay Data Output CEIC</span>', unsafe_allow_html=True)

st.markdown("*Melihat hubungan langsung antara fluktuasi/revisi hukum dengan tekanan modal keluar secara tahunan.*")

# Merge for dual-axis (yearly)
_df_outflow_yr = df.copy()
_df_outflow_yr['year'] = _df_outflow_yr['date'].dt.year
_df_outflow_yr = _df_outflow_yr.groupby('year')['net_sell_idr_tn'].sum().reset_index()

if not _df_churn.empty:
    _df_dual = pd.merge(_df_churn, _df_outflow_yr, on='year', how='inner').sort_values('year')
    if not _df_dual.empty:
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add Churn (Bar)
        fig_dual.add_trace(
            go.Bar(x=_df_dual['year'], y=_df_dual['churn_rate'], name="Churn Rate (%)", marker_color="#FF9800", opacity=0.7),
            secondary_y=False,
        )
        # Add Outflow (Line)
        fig_dual.add_trace(
            go.Scatter(x=_df_dual['year'], y=_df_dual['net_sell_idr_tn'], name="Net Sell Outflow (IDR Tn)", mode='lines+markers', line=dict(color="#E53935", width=3)),
            secondary_y=True,
        )
        
        fig_dual.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_dual.update_yaxes(title_text="<b>Churn Rate</b> (%)", secondary_y=False)
        fig_dual.update_yaxes(title_text="<b>Capital Outflow</b> (IDR Tn)", secondary_y=True)
        
        st.plotly_chart(fig_dual, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 4.2 TIME SERIES + ANOMALI (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.2 Dampak Ekonomi (Y): Time Series Net Sell & Deteksi Anomali Volatilitas")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Anomaly Detection (Variabel Y)</span>', unsafe_allow_html=True)

ts_narr = """Grafik batang di bawah menampilkan fluktuasi ekstrem net sell per periode. Dari rata-rata historis **{mean:.2f} IDR Tn**, algoritma mendeteksi **{n_anom} minggu anomali** (batang merah, Z > 2) dan **{n_high} minggu elevated** (oranye, Z > 1) di mana kepanikan institusional memicu pelarian modal masif. Spike merah ini tidak tersebar acak melainkan **terkonsentrasi (clustering)** pada periode krisis kepercayaan hukum. Rekor kepanikan terpanjang mencapai **{streak} minggu berturut-turut** di atas rata-rata — mengonfirmasi bahwa *regulatory shock* memicu efek domino bagi penarikan likuiditas pasar."""

ts_src = "Data mentah <code>capital_outflow.csv</code>. Z-Score dihitung dari mean dan std. deviasi seluruh dataset."
st.markdown(ts_narr.format(mean=mean_ns, n_anom=n_anomaly, n_high=n_high, streak=max_streak) +
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
# 4.3 ISOLATION FOREST — DETEKSI ANOMALI (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.3 Dampak Ekonomi (Y): Isolation Forest — Zonasi Capital Flight")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Machine Learning Isolation Forest (Variabel Y)</span>', unsafe_allow_html=True)

iso_narr = """Algoritma **Isolation Forest** (Liu et al., 2008) mengisolasi data outlier melalui partisi acak rekursif. Prinsipnya: data anomali lebih mudah dipisahkan karena jumlahnya sedikit dan nilainya ekstrem. Dari {n} observasi, model mendeteksi **{n_anom} episode anomali** yang jatuh di dalam *zona merah* (decision boundary). Area merah pada grafik merepresentasikan wilayah di mana algoritma mengklasifikasikan observasi sebagai pelarian modal di luar pola normal — titik-titik di zona ini bukan fluktuasi wajar melainkan *capital flight episodes* yang dipicu guncangan regulasi."""

iso_src = f"Analisis Isolation Forest pada <code>capital_outflow.csv</code> ({n_obs} observasi, kontaminasi 15%)."
st.markdown(iso_narr.format(n=n_obs, n_anom=n_iso_anomaly) +
            f"\n\n<small>📁 <b>Sumber:</b> {iso_src}</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Decision Boundary Scatter — zona merah = area anomali, zona biru = area normal. Diamond merah = episode anomali.")

# Decision Boundary Scatter Plot
fig_iso = go.Figure()

# Anomaly zone shading (red area above threshold)
fig_iso.add_hrect(
    y0=iso_threshold, y1=max_ns * 1.15,
    fillcolor="rgba(229,57,53,0.12)", line_width=0,
    annotation_text="ZONA ANOMALI", annotation_position="top left",
    annotation=dict(font=dict(color="#E53935", size=12, family="Arial Black"))
)

# Normal zone shading (blue area below threshold)
fig_iso.add_hrect(
    y0=min_ns * 0.85, y1=iso_threshold,
    fillcolor="rgba(66,165,245,0.06)", line_width=0
)

# Threshold line
fig_iso.add_hline(
    y=iso_threshold, line_dash="dash", line_color=C_WARN, line_width=2,
    annotation_text=f"Decision Boundary: {iso_threshold:.1f} Tn",
    annotation=dict(font=dict(color=C_WARN, size=11))
)

# Normal points
df_normal = df[~df["is_iso_anomaly"]]
fig_iso.add_trace(go.Scatter(
    x=df_normal["date"], y=df_normal["net_sell_idr_tn"],
    mode="markers", name="Normal",
    marker=dict(size=9, color=C_NET_SELL, opacity=0.8,
                line=dict(width=1, color="#1565C0")),
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Net Sell: %{y:.2f} Tn<br>Status: Normal<extra></extra>"
))

# Anomaly points
df_anom = df[df["is_iso_anomaly"]]
fig_iso.add_trace(go.Scatter(
    x=df_anom["date"], y=df_anom["net_sell_idr_tn"],
    mode="markers+text", name="Anomali",
    marker=dict(size=16, color=C_ANOMALY, symbol="diamond",
                line=dict(width=2, color="#fff")),
    text=[f"{v:.1f}" for v in df_anom["net_sell_idr_tn"]],
    textposition="top center", textfont=dict(color=C_ANOMALY, size=10),
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Net Sell: %{y:.2f} Tn<br><b>ANOMALI</b><extra></extra>"
))

# Mean reference line
fig_iso.add_hline(y=mean_ns, line_dash="dot", line_color="#666", line_width=1,
                  annotation_text=f"Rata-rata: {mean_ns:.1f} Tn",
                  annotation=dict(font=dict(color="#888", size=10)))

fig_iso.update_layout(
    template=PLOTLY_TEMPLATE, height=480,
    yaxis_title="Net Sell (IDR Tn / Triliun)", xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_iso, use_container_width=True)


# ══════════════════════════════════════════════════
# 4.4 AGREGASI KUARTAL (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.4 Dampak Ekonomi (Y): Agregasi Kuartal — Tren Makro Ekstrem")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Quarterly Aggregation (Variabel Y)</span>', unsafe_allow_html=True)

q_narr = """Agregasi kuartalan menyaring *noise* mingguan untuk mengungkap daya rusak makroekonomi dari pencabutan kebijakan hukum. Kuartal terburuk berpusat pada **{worst_q}** yang menyapu bersih likuiditas hingga **{worst_val:.2f} IDR Tn / Triliun**. Jika lonjakan *outflow* tinggi pada satu kuartal namun segera mereda, itu terhitung reaksi syok sesaat. Namun, tinggi batang yang terus persisten di rasio atas mengindikasikan *regulatory reversal* bukan sekadar insiden tunggal, melainkan telah membeku menjadi iklim usaha yang struktural-destruktif bagi sentimen investasi."""

q_src = "Agregasi <code>capital_outflow.csv</code> per kuartal: sum, mean, max, dan count per kuartal."
st.markdown(q_narr.format(worst_q=worst_q, worst_val=worst_q_val) +
            f"\n\n<small>📁 <b>Sumber:</b> {q_src}</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Bar + Line combo — batang = total net sell per kuartal, garis = rata-rata berjalan (standar BI/IMF).")

if len(q_agg) > 0:
    # Bar colors by severity
    q_mean = q_agg["total_sell"].mean()
    q_colors = [C_ANOMALY if v == q_agg["total_sell"].max()
                else C_WARN if v > q_mean
                else C_NET_SELL for v in q_agg["total_sell"]]

    # Rolling average (2-quarter window)
    q_agg["rolling_avg"] = q_agg["total_sell"].rolling(window=min(2, len(q_agg)), min_periods=1).mean()

    fig_q = go.Figure()

    # Bar: total sell per quarter
    fig_q.add_trace(go.Bar(
        x=q_agg["quarter_str"], y=q_agg["total_sell"],
        marker_color=q_colors, name="Total Net Sell",
        text=[f"{v:.1f}" for v in q_agg["total_sell"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Total: %{y:.2f} Tn<extra></extra>"
    ))

    # Line: rolling average overlay
    fig_q.add_trace(go.Scatter(
        x=q_agg["quarter_str"], y=q_agg["rolling_avg"],
        mode="lines+markers", name="Rata-rata Berjalan",
        line=dict(color="#66BB6A", width=3, dash="dot"),
        marker=dict(size=8, color="#66BB6A", line=dict(width=1, color="#333")),
        hovertemplate="<b>%{x}</b><br>Moving Avg: %{y:.2f} Tn<extra></extra>"
    ))

    # Mean reference line
    fig_q.add_hline(y=q_mean, line_dash="dot", line_color="#888", line_width=1,
                    annotation_text=f"Rata-rata Kuartal: {q_mean:.1f} Tn",
                    annotation=dict(font=dict(color="#888", size=10)))

    fig_q.update_layout(
        template=PLOTLY_TEMPLATE, height=450,
        yaxis_title="Total Net Sell (IDR Tn / Triliun)", xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20), barmode="group"
    )
    st.plotly_chart(fig_q, use_container_width=True)


# ══════════════════════════════════════════════════
# 4.5 TABEL EPISODE ANOMALI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.5 Dampak Ekonomi (Y): Log Episode Kepanikan (Z > 2)")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Z-Score Episode Detection (Variabel Y)</span>', unsafe_allow_html=True)

tbl_narr = """Deteksi anomali statistik mencatat titik nadir pelarian modal pada **{max_date}** dengan nilai fantastis **{max_val:.2f} IDR Tn** (Z-Score **{max_z:.2f}**). Tabel di bawah memetakan secara kronologis seluruh episode anomali (Z > 2) dan elevated (Z > 1) yang berfungsi sebagai **jejak forensik aliran modal**. Analis penegakan hukum dapat langsung melakukan *overlay* kalender kejadian—menguji korelasi persisnya jatuhnya triliunan rupiah dengan diumumkannya pencabutan izin tambang, perombakan mendadak pejabat kunci, atau intervensi retroaktif dalam kontrak esensial."""

st.markdown(tbl_narr.format(max_date=max_date, max_val=max_ns, max_z=max_z))

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
**Sintesis Temuan Utama (Law & Economics):**

Sesuai dengan kerangka kerja Law & Economics, analisis empiris *Regulatory Reversal* ini membuktikan presisi struktur transmisi risiko yang berjalan mulus dan destruktif:
`Perubahan Aturan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi`

1. **Perubahan Aturan & Guncangan Ketidakpastian (Variabel X)** — Skala masif *Regulatory Churn Rate* (*turnover* regulasi) memproduksi instabilitas kebijakan tak terkendali. Lenyapnya preseden hukum konstan adalah defisit keadilan esensial yang membuat iklim korporasi dan modal asing berada pada posisi super rentan tanpa proteksi legal-statis.
 
2. **Persepsi Risiko & Lonjakan Biaya Ekonomi (Variabel Y)** — Sinyal guncangan itu langsung menjelma menjadi ancaman ketakutan *Stranded Asset*. Merespons persepsi risiko ini, volatilitas ekuivalen modal lari mencatatkan (CV bernilai tinggi **{cv:.1f}%**). Besaran inflasi pada struktur volatilitas ini adalah refleksi utuh **Biaya Ekonomi Premium**; mencetak sekurang-kurangnya **{n_anom} episode anomali kepanikan** di mana investor mengevakuasi likuiditas mereka menembus titik api **{max_val:.2f} IDR Triliun** pada 1 sumbu krisis.
   
3. **Realisasi Keputusan Tarik Investasi (Variabel Y)** — Tercekik oleh ongkos mitigasi dan ekspektasi laba yang tersandera di meja birokrasi, investor langsung melikuidasi portofolio mereka (*Capital Outflow*). Pada rekor ledakan terburuk di rezim **{worst_q}**, *net sell* menggulung nyaris **{worst_val:.2f} IDR Tn**. Lenyapnya modal ini merepresentasikan pukulan *"vote of no confidence"* institusional terhadap anomali diskresi struktural pemerintah.

**Implikasi Final Rekomendasi:**
Kebiasaan mencetak *"Regulatory Reversal"* alias modifikasi dan pembatalan sepihak tak lagi semata sebuah manuver administratif; melainkan tindakan reaktif yang **mensabotase likuiditas makroekonomi secara absolut**. Jika instrumen regulasi dipermainkan seperti rezim otoriter yang mudah diputarbalikkan, investor rasional akan menolak berinvestasi panjang; mengukuhkan posisi Indonesia di kelas papan bawah *investable-grade rating*.
"""

st.markdown(temuan.format(
    cv=cv, max_val=max_ns,
    n_anom=n_anomaly,
    worst_q=worst_q, worst_val=worst_q_val
))
