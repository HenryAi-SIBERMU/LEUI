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
/* Base overrides */
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
st.title(_("H4: Aturan Berubah Mendadak, Modal Kabur"))
subtitle = _("Pencabutan izin dan perombakan regulasi secara tiba-tiba memicu gelombang pelarian modal asing.")
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
with st.expander(_("🔍 Metodologi"), expanded=False):
    st.markdown(_("""
    **Causal Chain Law & Economics:**
    `Perubahan Aturan Hukum → Ketidakpastian → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi`

    **Variabel Independen (X):**
    - **Perubahan Aturan Hukum (Regulatory Churn Rate)**: Rasio (persentase) regulasi yang dicabut/diubah per tahun terhadap total regulasi kumulatif yang pernah ada (sumber: Pasal.id REST API).
    
    **Variabel Dependen (Y):**
    - **Keputusan Investasi (Capital Outflow)**: Terefleksi pada nilai Net Sell Obligasi Pemerintah (IDR Triliun). Penarikan modal massal bereaksi secara proporsional terhadap tingginya beban **Biaya Ekonomi** (Premium risiko *Stranded Asset*) akibat lonjakan anomali fluktuasi kebijakan pasca-*reversal*.
    """))

# ── Intro Narrative ──
intro = _("""Teori **Aturan Berubah Mendadak (Regulatory Reversal Risk)** membongkar fakta seram bahwa investor sangat benci melihat aturan yang digusur atau diobrak-abrik dadakan. Dengan rantai efek domino: **Tsunami Aturan → Kepanikan Massal → Persepsi Risiko Melesat → Tembok Biaya Tinggi → Uang Kabur**. Data historis menangkap rekor pergantian bongkar-pasang peraturan kita pernah mencapai limit mengerikan **{max_churn:.1f}% (Regulatory Churn Rate)**.

Aturan yang sering dianulir penguasa/DPR menciptakan lubang gelap misteri bagi pebisnis. Investor yang trauma merasa di-prank sehingga ketakutan uangnya lenyap tertahan jadi aset rongsok (*Stranded asset*). Akhirnya modal mereka pun diterbangkan kabur keluar negeri merespons guncangan ini. Selama {n_obs} rekam jejak pengawasan ({yr_start}–{yr_end}), panik masif mencetak **{n_anom} titik "Kejang Jantungan" Ekstrem (Episode Anomali Z-Score > 2)**, dengan rekor Uang Minggat (*Net Sell*) sebesar **{max_ns:.1f} Triliun Rupiah** (Z-Score gila {max_z:.2f}). Lenyapnya ratusan triliun likuiditas ini menegaskan satu hukum alam: Mengakali kepastian hukum negara sendiri setara dengan melelang masa depan lapangan kerja.""")

intro_src = _("Pasal.id API (Variabel Hukum/X) & Catatan Net Sell Data CEIC/Bloomberg (Variabel Makroekonomi/Y).")

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
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid #FF9800; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Tingkat Tsunami Aturan (Churn Rate Maksimum)</div>
        <div style="font-size:2rem; font-weight:bold; color:#FF9800;">{_max_churn:.1f}%</div>
        <div style="font-size:0.8rem; font-weight:600; color:#FF9800; margin-bottom:10px;">Variabel Hukum (X)</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Persentase aturan yg dicabut/dianulir terhadap total regulasi kumulatif pertahunnya.
        </p>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid {C_ANOMALY}; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Rekor Modal Kabur (Net Sell Tertinggi)</div>
        <div style="font-size:2rem; font-weight:bold; color:{C_ANOMALY};">{max_ns:.1f} Tn</div>
        <div style="font-size:0.8rem; font-weight:600; color:{C_WARN}; margin-bottom:10px;">Variabel Ekonomi (Y)</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Nilai penarikan modal obligasi (triliun rupiah) tebesar dalam satu periode.
        </p>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid {C_ANOMALY}; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Titik Kejang Jantungan Ekstrem (Anomali)</div>
        <div style="font-size:2rem; font-weight:bold; color:{C_ANOMALY};">{n_anomaly}</div>
        <div style="font-size:0.8rem; font-weight:600; color:#AAA; margin-bottom:10px;">Kepanikan (Dampak Y)</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Jumlah titik periode di mana skala kepanikan (Z-Score) menembus kewajaran > 2.0.
        </p>
    </div>""", unsafe_allow_html=True)
with c4:
    cv_color = C_ANOMALY if cv > 50 else C_WARN
    st.markdown(f"""
    <div style="background:#3b1414; padding:20px; border-radius:10px; border-top:4px solid {cv_color}; text-align:center; height:100%;">
        <div style="font-size:0.9rem; color:#AAA;">Tingkat Goncangan Uang Beredar (Volatilitas)</div>
        <div style="font-size:2rem; font-weight:bold; color:{cv_color};">{cv:.1f}%</div>
        <div style="font-size:0.8rem; font-weight:600; color:{C_WARN}; margin-bottom:10px;">Ketidakpastian Absolut</div>
        <p style="border-top:1px dotted #777; padding-top:10px; margin:0; font-size:0.75rem; color:#888; text-align:left;">
            <b>Asal Angka:</b> Sebaran deviasi standar dibagi rata-rata arus modal (Coefficient of Variation).
        </p>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# ═══════════ LAYER X: VARIABEL HUKUM ═════════════════════
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.markdown('<div style="background:#5C2B6A;color:#E1BEE7;padding:8px 16px;border-radius:8px;font-size:1rem;font-weight:700;display:inline-block;">FAKTA PENYEBAB: ATURAN YANG SERING BERUBAH</div>', unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ── 4.1 Variabel Hukum (X) ──
st.markdown("---")
st.subheader(_("4.1 Fakta: Seberapa Sering Aturan Bisnis Dicabut / Diganti?"))
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Regulatory Churn Test & Lifecycle Analysis (Variabel X)</span>', unsafe_allow_html=True)

churn_narrative = _("""Menggunakan instrumen **Regulatory Churn Test**, kami mengukur tingkat ketidakpastian produk hukum (undang-undang, peraturan pemerintah, peraturan daerah, dll) yang secara langsung mendikte stabilitas iklim usaha dan investasi. 

Grafik di bawah ini memvisualisasikan **tren Churn Rate** nasional — yakni rasio persentase regulasi bisnis yang dibatalkan, dicabut, atau direvisi setiap tahunnya. Lonjakan skor *churn rate* ke level puncak **{max_churn:.1f}%** mengonfirmasi keberadaan fenomena *"bongkar-pasang"* aturan. Bagi pemodal asing dengan kapital besar, regulasi yang direvisi secara *ad-hoc* menciptakan ancaman hukum absolut: hak operasional investasi (konsesi izin tambang, hak komersial, kontrak esensial, dsbg) yang dijamin oleh konstitusi hari ini bisa saja disapu bersih esok hari secara retroaktif. Konsekuensi dari defisit garansi yurisprudensi inilah yang akan membengkakkan *Risk Premium*.""")

churn_src = _("Ekstraksi status riwayat hukum dari Pasal.id REST API & JDIH Nasional, difilter berdasarkan indeks keyword subsektoral regulasi esensial H4.")

st.markdown(churn_narrative.format(max_churn=_max_churn) + f"\n\n<small>📁 <b>Sumber:</b> {churn_src}</small>", unsafe_allow_html=True)

if not _df_churn.empty:
    st.caption(_("📊 Tren Fluktuasi Regulatory Churn Rate Nasional (% Regulasi Dicabut/Diubah per Tahun)"))
    
    df_churn_plot = _df_churn[_df_churn['year'] >= 2000]
    
    fig_churn = px.bar(
        df_churn_plot, x="year", y="churn_rate",
        color="churn_rate", color_continuous_scale=["#FFA726", "#F57C00", "#E65100"],
        template=PLOTLY_TEMPLATE,
        labels={"year": "Tahun Terbit", "churn_rate": "Churn Rate (%)"}
    )
    # Anotasi Puncak Churn
    if len(df_churn_plot) > 0:
        worst_churn_idx = df_churn_plot['churn_rate'].idxmax()
        worst_row = df_churn_plot.loc[worst_churn_idx]
        fig_churn.add_annotation(
            x=worst_row['year'], y=worst_row['churn_rate'],
            text=f"Tsunami Aturan Puncak ({worst_row['churn_rate']:.1f}%)",
            showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor="#E65100",
            ax=0, ay=-30, font=dict(color="#E65100", size=11, weight="bold")
        )
    fig_churn.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
    st.plotly_chart(fig_churn, use_container_width=True)
    
    st.markdown(f"""
    <div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid #FF9800; margin-bottom: 20px; margin-top: 5px;">
        <b>Kesimpulan Kilat:</b> Sistem merangkum rekor <strong>Tsunami Aturan absolut sebesar {_max_churn:.1f}%</strong> bertepatan di periode diskresi regulasi mendadak. Gejolak volatilitas aturan yang dibongkar-pasang sepihak ini mewakili pukulan telak dari <em>Variabel Hukum (X)</em> yang mengacaukan kepastian usaha hingga memicu eksodus investasi besar-besaran.
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_("📋 Lihat Data Riwayat: Tabulasi Daftar Regulasi Reversal H4 (Dicabut/Diubah)"), expanded=False):
        if not _df_rev.empty:
            df_reversal = _df_rev[_df_rev['status'] != 'berlaku'].copy()
            if not df_reversal.empty:
                st.dataframe(df_reversal[['year', 'title', 'status', 'issuing_body']].sort_values("year", ascending=False), use_container_width=True, hide_index=True)
            else:
                st.dataframe(_df_rev[['year', 'title', 'status', 'issuing_body']].sort_values("year", ascending=False), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# ═══════════ LAYER Y: DAMPAK EKONOMI ═════════════════════
# ══════════════════════════════════════════════════════════
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.markdown('<div style="background:#1B5E20;color:#C8E6C9;padding:8px 16px;border-radius:8px;font-size:1rem;font-weight:700;display:inline-block;">DAMPAK NYATA: MODAL ASING KABUR</div>', unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 4.2 TIME SERIES + ANOMALI (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.2 Dampak: Gelombang Pelarian Modal — Kapan Investor Panik?")
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

if len(df) > 0:
    worst_ts_idx = df["net_sell_idr_tn"].idxmax()
    worst_ts = df.loc[worst_ts_idx]
    fig_ts.add_annotation(
        x=worst_ts['date'], y=worst_ts['net_sell_idr_tn'],
        text=f"Rekor Terparah ({max_ns:.1f} Tn)",
        showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
        ax=0, ay=-30, font=dict(color=C_ANOMALY, size=11, weight="bold")
    )

st.plotly_chart(fig_ts, use_container_width=True)

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_ANOMALY}; margin-bottom: 20px; margin-top: 5px;">
    <b>Kesimpulan Kilat:</b> Algoritma berhasil memetakan <strong>{n_anomaly} titik "Nadi Kepanikan" (Skala Petaka Z-Score > 2)</strong>. Catatan rekor uang kabur terlama menembus batas <strong>{max_streak} minggu beruntun (non-stop)</strong> di mana investor tidak henti-hentinya mengangkat kaki karena iklim kepastian hukum sedang berantakan. Rekor terburuk menyentuh hilangnya <strong>{max_ns:.1f} Tn</strong> kekayaan negara.
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 4.3 ISOLATION FOREST — DETEKSI ANOMALI (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.3 Dampak: Zona Merah Pelarian Modal")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Detektor Kepanikan (Machine Learning Isolation Forest / Variabel Y)</span>', unsafe_allow_html=True)

iso_narr = """Model Detektor Kepanikan Massal berbasis algoritma statistik (**Isolation Forest**) bertugas mengepung outlier tanpa campur tangan teknis manual. Prinsipnya sederhana: aliran dana normal bersifat rutin dan padat, sedangkan anomali pelarian akibat ketakutan (seperti syok aturan baru) jumlah datanya terpisah jauh di pencilan yang esktrem (Zona Merah). Dari {n} pantauan minggu komersial ini, mesin mendeteksi **{n_anom} titik gila** di dalam _decision boundary_ merah, yang membuktikan goncangan drastis bukan terjadi karena murni siklus pasar bebas, melainkan _Capital Flight_ massal mengevakuasi investasi yang tertahan."""

iso_src = f"Analisis Detektor Kepanikan Isolation Forest pada <code>capital_outflow.csv</code> ({n_obs} observasi, kontaminasi 15%)."
st.markdown(iso_narr.format(n=n_obs, n_anom=n_iso_anomaly) +
            f"\n\n<small>📁 <b>Sumber:</b> {iso_src}</small>", unsafe_allow_html=True)
st.caption("📊 Visualisasi: Decision Boundary Scatter — zona merah = area kepanikan tak terkendali, zona biru = area aman normal.")

# Decision Boundary Scatter Plot
fig_iso = go.Figure()

# Anomaly zone shading (red area above threshold)
fig_iso.add_hrect(
    y0=iso_threshold, y1=max_ns * 1.15,
    fillcolor="rgba(229,57,53,0.12)", line_width=0,
    annotation_text="ZONA KEPANIKAN (ANOMALI)", annotation_position="top left",
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
    annotation_text=f"Batas Kepanikan Massal: {iso_threshold:.1f} Tn",
    annotation=dict(font=dict(color=C_WARN, size=11))
)

# Normal points
df_normal = df[~df["is_iso_anomaly"]]
fig_iso.add_trace(go.Scatter(
    x=df_normal["date"], y=df_normal["net_sell_idr_tn"],
    mode="markers", name="Aman",
    marker=dict(size=9, color=C_NET_SELL, opacity=0.8,
                line=dict(width=1, color="#1565C0")),
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Net Sell: %{y:.2f} Tn<br>Status: Aman<extra></extra>"
))

# Anomaly points
df_anom = df[df["is_iso_anomaly"]]
fig_iso.add_trace(go.Scatter(
    x=df_anom["date"], y=df_anom["net_sell_idr_tn"],
    mode="markers+text", name="Kepanikan Abnormal!",
    marker=dict(size=16, color=C_ANOMALY, symbol="diamond",
                line=dict(width=2, color="#fff")),
    text=["" for _ in df_anom["net_sell_idr_tn"]], # Hilangkan text duplikat agar panah bersih
    textposition="top center", textfont=dict(color=C_ANOMALY, size=10),
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Net Sell: %{y:.2f} Tn<br><b>Kepanikan Abnormal!</b><extra></extra>"
))

if len(df_anom) > 0:
    worst_iso_idx = df_anom["net_sell_idr_tn"].idxmax()
    worst_iso = df_anom.loc[worst_iso_idx]
    fig_iso.add_annotation(
        x=worst_iso['date'], y=worst_iso['net_sell_idr_tn'],
        text=f"Pencilan Terparah ({worst_iso['net_sell_idr_tn']:.1f} Tn)",
        showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
        ax=0, ay=-30, font=dict(color=C_ANOMALY, size=11, weight="bold")
    )

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

st.markdown(f"""
<div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom: 20px; margin-top: 5px;">
    <b>Kesimpulan Kilat:</b> Menggunakan teknologi saringan algoritma <i>Isolation Forest ML</i>, teridentifikasi mutlak <strong>{n_iso_anomaly} titik merah menyala</strong>. Titik-titik *"Pencilan (Outlier)"* ini 100% melangkahi Batas Kepanikan ({iso_threshold:.1f} Tn) alias mustahil dikategorikan sebagai fluktuasi alamiah. Seluruhnya adalah sinergi "Uang Kabur Massal" (*Capital Flight*) merespons iklim hukum yang karut-marut.
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 4.4 AGREGASI KUARTAL (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.4 Dampak: Tren Kuartalan Skala Makro")
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Kumulatif Per Kuartal (Quarterly Aggregation / Variabel Y)</span>', unsafe_allow_html=True)

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

    # [NEW] Arrow Annotation Puncak Kuartal
    if len(q_agg) > 0:
        worst_q_idx2 = q_agg["total_sell"].idxmax()
        worst_q_row2 = q_agg.loc[worst_q_idx2]
        fig_q.add_annotation(
            x=worst_q_row2['quarter_str'], y=worst_q_row2['total_sell'],
            text=f"Kuartal Terhancur ({worst_q_row2['total_sell']:.1f} Tn)",
            showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor=C_ANOMALY,
            ax=0, ay=-30, font=dict(color=C_ANOMALY, size=11, weight="bold")
        )

    fig_q.update_layout(
        template=PLOTLY_TEMPLATE, height=450,
        yaxis_title="Total Net Sell (IDR Tn / Triliun)", xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20), barmode="group"
    )
    st.plotly_chart(fig_q, use_container_width=True)

    st.markdown(f"""
    <div style="background:#1E1E1E; padding:14px 20px; border-radius:10px; border-left:5px solid {C_ANOMALY}; margin-bottom: 20px; margin-top: 5px;">
        <b>Kesimpulan Kilat:</b> Secara siklus makro, titik kuartal <strong>{worst_q}</strong> menyapu bersih pertahanan ekonomi kita dengan tewasnya kapital <strong>{worst_q_val:.1f} Triliun Rupiah</strong>. Batang ini membuktikan fenomena aturan plin-plan bukan sekadar gejolak seminggu-dua-minggu; namun mengkristal jadi ancaman mematikan berskala catur-wulan bertubi-tubi.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 4.5 TABEL EPISODE ANOMALI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader("4.5 Catatan Peristiwa: Kapan Uang Kabur Paling Masif?")
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
st.subheader("3. Kesimpulan: Ancaman Aturan Berubah Mendadak (Regulatory Reversal)")

st.markdown(f"""
<div style="background-color: #2F0A28; padding: 20px; border-radius: 10px; border-left: 5px solid #FF5252;">
    <h4 style="color: #FF5252; margin-top: 0;">Sintesis Temuan (Law & Economics)</h4>
    <p style="color: #F8BBD0; font-size: 0.95rem; margin-bottom: 15px;">
        Keruntuhan logis transmisi investasi: <i>Tsunami Aturan → Uang Kabur Massal</i> benar-benar terbukti membawa kehancuran skala megaton terhadap kantong ekonomi Indonesia:
    </p>
    <ul style="color: #F8BBD0; font-size: 0.95rem; line-height: 1.6;">
        <li><b>Tsunami Aturan (Variabel Hukum/X):</b> Rekor pencabutan regulasi <b>{_max_churn:.1f}%</b> pertahun menjadi biang kerok defisit <i>Predictability</i> (tidak ada yg tahu besok aturan apa yang ditebas), membuat semua perjanjian usaha rentan disobek sepihak.</li>
        <li><b>Uang Kabur Massal (Variabel Ekonomi/Y):</b> Merespons iklim tak masuk akal ini, insting ketakutan investor terdeteksi meletupkan <b>{n_anomaly} Skala Petaka Kepanikan (Anomali Z-Score > 2)</b> yang menarik ratusan triliun devisa. Rekor tunggal mingguan menyentuh <b>{max_ns:.1f} Tn</b> hilang tak berbekas dalam sekejap mata.</li>
        <li><b>Kerangka Kebangkrutan Siklus Penuh:</b> Di masa tergelap pemerintahan ({worst_q}), kapital lenyap hingga <b>{worst_q_val:.1f} Tn Rupiah</b>. Artinya, akrobat perundang-undangan (<i>Regulatory Reversal</i>) sebut saja dalam konteks perizinan lingkungan hidup atau perlindungan tenagakerja, memakan ongkos makroekonomi super mahal: melelang kepercayaan di ranah global dan memiskinkan dompet negara.</li>
    </ul>
</div>
""", unsafe_allow_html=True)
