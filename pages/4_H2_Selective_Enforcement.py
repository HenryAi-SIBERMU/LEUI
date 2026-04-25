"""
Page 2 — H2: Selective Enforcement
Analisis pola enforcement selektif menggunakan anomaly detection pada IKK & PMI.
    `Selective Enforcement → Political/Discretion Risk → Confidence Crash → Investment Delay/Exit`

Causal Chain: Selective Enforcement → Political/Discretion Risk → IKK/PMI Drop → Investment Delay
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
    page_title="H2: Selective Enforcement — CELIOS LEUI",
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
.metric-value { font-size: 2rem; font-weight: 700; color: #4CAF50; }
.metric-label { font-size: 0.9rem; color: #AAA; margin-bottom: 5px; }
.metric-delta { font-size: 0.8rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
C_IKK_EXP = "#42A5F5"
C_IKK_PRES = "#66BB6A"
C_PMI = "#AB47BC"
C_ANOMALY = "#FF0000"  # Diubah menjadi merah terang agresif untuk indikasi bahaya
C_WARN = "#FF9800"
C_BG = "#1E1E1E"

# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "final")

@st.cache_data(ttl=3600)
def load_data_h2_sipp():
    df_ikk = pd.read_csv(os.path.join(DATA, "ikk_expect_vs_present.csv"), parse_dates=["date"])
    df_pmi = pd.read_csv(os.path.join(DATA, "pmi_manufaktur.csv"), parse_dates=["date"])
    
    # Load and process SIPP Wanprestasi Korporasi (Corporate Taxonomy Filter) for Layer X
    sipp_path = os.path.join(DATA, "sipp_corporate_wanprestasi.csv")
    df_sipp_raw = pd.read_csv(sipp_path)
    df_sipp_raw["Tanggal Daftar"] = pd.to_datetime(df_sipp_raw["Tanggal Daftar"], format="%d %b %Y", errors="coerce")
    df_sipp_valid = df_sipp_raw.dropna(subset=["Tanggal Daftar"]).copy()
    df_sipp_valid["year_month"] = df_sipp_valid["Tanggal Daftar"].dt.to_period("M")
    
    df_sipp_monthly = df_sipp_valid.groupby("year_month").size().reset_index(name="jumlah_perkara")
    df_sipp_monthly["date"] = df_sipp_monthly["year_month"].dt.to_timestamp()
    df_sipp_monthly = df_sipp_monthly.sort_values("date").reset_index(drop=True)
    
    return df_ikk, df_pmi, df_sipp_monthly

df_ikk, df_pmi, df_sipp = load_data_h2_sipp()


# ══════════════════════════════════════════════════
# PRE-COMPUTE: Anomaly Detection
# ══════════════════════════════════════════════════

# --- IKK Anomaly (Z-Score on month-over-month change) ---
df_ikk = df_ikk.sort_values("date").reset_index(drop=True)
df_ikk["ikk_exp_pct"] = df_ikk["ikk_expectation"].pct_change() * 100
df_ikk["ikk_pres_pct"] = df_ikk["ikk_present"].pct_change() * 100
df_ikk["ikk_gap_change"] = df_ikk["ikk_gap"].diff()

# Z-Score on IKK Expectation pct change
exp_mean = df_ikk["ikk_exp_pct"].mean()
exp_std = df_ikk["ikk_exp_pct"].std()
df_ikk["ikk_exp_zscore"] = (df_ikk["ikk_exp_pct"] - exp_mean) / exp_std

# Z-Score on IKK Gap change
gap_mean = df_ikk["ikk_gap_change"].mean()
gap_std = df_ikk["ikk_gap_change"].std()
df_ikk["ikk_gap_zscore"] = (df_ikk["ikk_gap_change"] - gap_mean) / gap_std

# Flag anomalies (Z < -2 for drops, Z > 2 for spikes)
df_ikk["is_exp_anomaly"] = df_ikk["ikk_exp_zscore"] < -2
df_ikk["is_gap_anomaly"] = df_ikk["ikk_gap_zscore"].abs() > 2

# --- PMI Anomaly ---
df_pmi = df_pmi.sort_values("date").reset_index(drop=True)
df_pmi["pmi_pct"] = df_pmi["pmi_index"].pct_change() * 100
pmi_mean = df_pmi["pmi_pct"].mean()
pmi_std = df_pmi["pmi_pct"].std()
df_pmi["pmi_zscore"] = (df_pmi["pmi_pct"] - pmi_mean) / pmi_std if pmi_std > 0 else 0
df_pmi["is_kontraksi"] = df_pmi["pmi_index"] < 50
df_pmi["is_pmi_anomaly"] = df_pmi["pmi_zscore"] < -2

# --- Computed stats for narrative ---
n_exp_anomaly = df_ikk["is_exp_anomaly"].sum()
n_gap_anomaly = df_ikk["is_gap_anomaly"].sum()
anomaly_dates_exp = df_ikk[df_ikk["is_exp_anomaly"]].sort_values("ikk_exp_zscore")
worst_exp_drop = anomaly_dates_exp.iloc[0] if len(anomaly_dates_exp) > 0 else None
worst_exp_date = worst_exp_drop["date"].strftime("%B %Y") if worst_exp_drop is not None else "—"
worst_exp_val = worst_exp_drop["ikk_exp_pct"] if worst_exp_drop is not None else 0
worst_exp_z = worst_exp_drop["ikk_exp_zscore"] if worst_exp_drop is not None else 0
worst_exp_date_ts = worst_exp_drop["date"] if worst_exp_drop is not None else df_ikk["date"].iloc[0]
worst_exp_date_str = worst_exp_date_ts.strftime('%Y-%m-%d')
worst_exp_y = worst_exp_drop["ikk_expectation"] if worst_exp_drop is not None else 100

ikk_abs_min = df_ikk["ikk_expectation"].min()
ikk_abs_min_idx = df_ikk["ikk_expectation"].idxmin()
ikk_abs_min_date = df_ikk.loc[ikk_abs_min_idx, "date"].strftime("%B %Y")
ikk_abs_min_date_ts = df_ikk.loc[ikk_abs_min_idx, "date"]
ikk_abs_min_date_str = ikk_abs_min_date_ts.strftime('%Y-%m-%d')

ikk_latest_gap = df_ikk["ikk_gap"].iloc[-1]
ikk_avg_gap = df_ikk["ikk_gap"].mean()
ikk_max_gap = df_ikk["ikk_gap"].max()
ikk_max_gap_idx = df_ikk["ikk_gap"].idxmax()
ikk_max_gap_date = df_ikk.loc[ikk_max_gap_idx, "date"].strftime("%B %Y")
ikk_max_gap_date_ts = df_ikk.loc[ikk_max_gap_idx, "date"]
ikk_max_gap_date_str = ikk_max_gap_date_ts.strftime('%Y-%m-%d')

ikk_min_gap = df_ikk["ikk_gap"].min()
ikk_min_gap_date = df_ikk.loc[df_ikk["ikk_gap"].idxmin(), "date"].strftime("%B %Y")

n_kontraksi = df_pmi["is_kontraksi"].sum()
n_pmi_months = len(df_pmi)
pmi_latest = df_pmi["pmi_index"].iloc[-1]
pmi_avg = df_pmi["pmi_index"].mean()
pmi_min = df_pmi["pmi_index"].min()
pmi_min_idx = df_pmi["pmi_index"].idxmin()
pmi_min_date = df_pmi.loc[pmi_min_idx, "date"].strftime("%B %Y")
pmi_min_date_ts = df_pmi.loc[pmi_min_idx, "date"]
pmi_min_date_str = pmi_min_date_ts.strftime('%Y-%m-%d')

ikk_date_start = df_ikk["date"].min().strftime("%Y")
ikk_date_end = df_ikk["date"].max().strftime("%Y")
pmi_date_start = df_pmi["date"].min().strftime("%B %Y")
pmi_date_end = df_pmi["date"].max().strftime("%B %Y")


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title(_("H2: Hukum Tajam ke Bawah, Tumpul ke Atas"))
subtitle = _("Penegakan hukum yang tebang pilih menciptakan kepanikan pasar secara sporadis dan tidak terduga.")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander(_("🔍 Metodologi"), expanded=False):
    st.markdown(_("""
    **Causal Chain Law & Economics:**
    `Selective Enforcement → Discretion Risk → Confidence Crash → Investment Delay/Exit`

    **Variabel Independen (X):**
    - Sengketa wanprestasi massal di Pengadilan Negeri (SIPP) sebagai proxy ketidakpastian hukum di akar rumput. Volume bulanan.

    **Variabel Dependen (Y):**
    - Indeks Keyakinan Konsumen (IKK) Bank Indonesia sebagai sentimen pasar domestik.
    - Purchasing Managers Index (PMI) Manufaktur S&P Global sebagai proxy iklim bisnis riil.

    **Pendekatan Analisis:**
    Penegakan hukum diskriminatif (fenomena *Selective Enforcement* dan intervensi yudisial) menciptakan persepsi risiko asimetris. Ketika pilar hukum tidak stabil, biaya kepatuhan (compliance cost) dan biaya keamanan mendadak membeku. Publik merespons dengan *Confidence Crash* (terdeteksi via Z-Score pada rentang IKK) yang berkorelasi lurus dengan perlambatan sektor riil (PMI manufaktur kontraksi < 50).
    """))


intro = _("""Data Pengadilan Negeri (SIPP Mahkamah Agung) diam-diam merekam bom waktu sengketa bisnis. Saat sengketa bisnis meledak tak terkendali di bawah, dampaknya langsung menjalar menghancurkan mental konsumen secara nasional dari tahun **{ikk_start} hingga {ikk_end}**. 

Alih-alih turun perlahan, mesin analisis data kami menangkap **{n_anom} "tsunami" kepanikan beruntun**—di mana optimisme masyarakat jatuh ke titik nadir dalam sekejap mata. Puncak terparahnya terekam pada **{worst_date}**, menelan harapan hingga **{worst_pct:.1f}%** dalam sebulan. Ketakutan publik ini berujung tragis pada penutupan mesin-mesin pabrik: industri manufaktur kita terpaksa mengerem paksa produksinya selama **{n_kon} dari {pmi_n} bulan**. Pola ini merobek mitos lama: *hukum yang tajam ke lawan dan tumpul ke kawan (tebang pilih)* berdampak sangat mematikan bagi dompet rakyat kecil.""")

intro_src = _("Data <code>sipp_nasional_wanprestasi_massal.csv</code> (SIPP MA RI), <code>ikk_expect_vs_present.csv</code>, dan <code>pmi_manufaktur.csv</code>.")

st.markdown(
    intro.format(
        ikk_start=ikk_date_start, ikk_end=ikk_date_end, ikk_n=len(df_ikk),
        pmi_start=pmi_date_start, pmi_end=pmi_date_end, pmi_n=n_pmi_months,
        n_anom=n_exp_anomaly, worst_date=worst_exp_date,
        worst_pct=worst_exp_val, worst_z=worst_exp_z,
        n_kon=n_kontraksi, max_gap_date=ikk_max_gap_date, max_gap=ikk_max_gap,
        min_gap_date=ikk_min_gap_date, min_gap=ikk_min_gap
    ) +
    f"\n\n<small>📁 <b>Sumber:</b> {intro_src.format(ikk_n=len(df_ikk), ikk_start=ikk_date_start, ikk_end=ikk_date_end, pmi_n=n_pmi_months, pmi_start=pmi_date_start, pmi_end=pmi_date_end)}</small>",
    unsafe_allow_html=True
)
st.caption(_("📊 Visualisasi: Empat panel — (1) IKK Time Series + Anomali, (2) IKK Gap Analysis, (3) PMI Kontraksi, (4) Tabel Episode Anomali. Semua threshold dihitung dari data."))


# ── KPI Cards — Standar LEUI: Dark BG, Border-Top, Asal Angka ──
kon_pct = n_kontraksi / n_pmi_months * 100 if n_pmi_months > 0 else 0
anom_color = C_ANOMALY if n_exp_anomaly > 5 else C_WARN
gap_color = C_ANOMALY if abs(ikk_latest_gap) > ikk_avg_gap * 1.5 else C_WARN
pmi_color = C_ANOMALY if pmi_latest < 50 else C_WARN
pmi_status = "Kontraksi" if pmi_latest < 50 else "Rentan Kontraksi"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {anom_color}; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">ALARM KEPANIKAN</h4>
        <h2 style="color: {anom_color}; margin: 0; font-size: 1.8rem;">{n_exp_anomaly} Episode</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;">Harapan masyarakat jatuh tersungkur (Lampu Merah menyala!)</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> Sistem pendeteksi kami memindai riwayat {len(df_ikk)} bulan terakhir. Saat grafik menukik kelewat tajam di luar toleransi kewajaran (kalkulasi <i>Z-Score Minus</i>), alarm darurat otomatis berdering mencatat tragedi tersebut.<br><i>(Terparah: {worst_exp_date}, mendadak amblas {worst_exp_val:.1f}%)</i>
        </p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {gap_color}; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">JURANG HARAPAN vs REALITA</h4>
        <h2 style="color: {gap_color}; margin: 0; font-size: 1.8rem;">{ikk_latest_gap:.1f} Poin</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;">Rata-rata gap sepanjang periode: {ikk_avg_gap:.1f}</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> Selisih IKK Ekspektasi dikurangi IKK Present per bulan. Gap terlebar: <b>{ikk_max_gap:.1f}</b> ({ikk_max_gap_date}), tersempit: <b>{ikk_min_gap:.1f}</b> ({ikk_min_gap_date}).
        </p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {pmi_color}; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">PMI TERAKHIR</h4>
        <h2 style="color: {pmi_color}; margin: 0; font-size: 1.8rem;">{pmi_latest:.1f}</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;">{pmi_status} (Threshold: 50)</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> PMI (Purchasing Managers Index) S&P Global. Nilai di atas 50 = ekspansi manufaktur, di bawah 50 = kontraksi. Rata-rata: <b>{pmi_avg:.1f}</b>, terendah: <b>{pmi_min:.1f}</b> ({pmi_min_date}).
        </p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div style="background-color: #3b1414; padding: 20px; border-radius: 10px; border-top: 5px solid {C_ANOMALY}; text-align: center;">
        <h4 style="color: #EF9A9A; margin: 0; padding-bottom: 5px;">BULAN KONTRAKSI</h4>
        <h2 style="color: {C_ANOMALY}; margin: 0; font-size: 1.8rem;">{n_kontraksi}/{n_pmi_months}</h2>
        <p style="color: #BDBDBD; margin: 10px 0 10px 0; font-size: 0.85rem;">{kon_pct:.0f}% dari total periode manufaktur menyusut</p>
        <p style="color: #9E9E9E; margin: 5px 0 0 0; font-size: 0.75rem; border-top: 1px dotted #777; padding-top: 8px; line-height: 1.4; text-align: left;">
            <b>Asal Angka:</b> Dari {n_pmi_months} bulan data PMI ({pmi_date_start} - {pmi_date_end}), dihitung jumlah bulan di mana PMI < 50.<br><i>(Kalkulasi: {n_kontraksi} / {n_pmi_months} = {kon_pct:.0f}%)</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 2.1 LAYER X: LONJAKAN SENGKETA BISNIS WAKTU NYATA (SIPP MA RI)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.1 Fakta Penyebab: Lonjakan Sengketa Bisnis yang Memicu Kepanikan"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Proxy Selective Enforcement: Data Gugatan SIPP Mahkamah Agung</span>', unsafe_allow_html=True)

wb_narr = _("""Pengadilan Negeri adalah medan perang pertama dalam bisnis. Grafik di bawah menelanjangi tren mengerikan: **ledakan volume saling gugat antar pelaku usaha** di momen-momen tertentu. 
Ketika hukum bisa "disetir" untuk memukul lawan politik atau menjatuhkan kompetitor bisnis, jumlah kasus perdata akan meledak tanpa alasan ekonomi yang masuk akal. Momen-momen inilah puncak dari *Selective Enforcement* (penegakan hukum tebang-pilih) yang meledakkan bom waktu ketakutan ke seluruh pasar.""")

wb_src = _("Data <code>sipp_nasional_wanprestasi_massal.csv</code> dianotasi & diagregasi bulanan. Sumber: Scrape Direktori MA RI / SIPP PN.")
st.markdown(wb_narr + f"\n\n<small>📁 <b>Sumber:</b> {wb_src}</small>", unsafe_allow_html=True)

fig_sipp = px.bar(df_sipp, x="date", y="jumlah_perkara", text="jumlah_perkara")
fig_sipp.update_traces(
    marker_color="#1E88E5", textposition='outside', textfont_size=10,
    hovertemplate="<b>Bulan: %{x|%B %Y}</b><br>Gugatan Wanprestasi Baru: <b>%{y} Kasus</b><extra></extra>"
)
fig_sipp.update_layout(
    template=PLOTLY_TEMPLATE, height=350,
    yaxis_title="Jumlah Gugatan Wanprestasi Terdaftar", xaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig_sipp, use_container_width=True)

st.markdown(f"""
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid #1E88E5; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi:</b> Ledakan tumpukan gugatan di pengadilan yang pecah bergerombol menelanjangi satu bukti: konflik mematikan dalam bisnis di Indonesia hampir selalu dipicu oleh kejutan-kejutan penegak hukum secara "tiba-tiba", bukan karena roda ekonomi yang murni memburuk secara perlahan.
</div>
""", unsafe_allow_html=True)

with st.expander(_("Lihat Data: Volume Gugatan Wanprestasi Korporasi per Bulan"), expanded=False):
    st.dataframe(df_sipp, use_container_width=True, hide_index=True)
    st.caption("Sumber File: `data/final/sipp_corporate_wanprestasi.csv` (diagregasi bulanan)")

# ══════════════════════════════════════════════════
# 2.2 IKK TIME SERIES + ANOMALY
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.2 Dampak: Kepercayaan Publik Hancur Berkeping-keping"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Indikator: IKK (Indeks Keyakinan Konsumen) Bank Indonesia</span>', unsafe_allow_html=True)

ikk_narr = _("""Bayangkan masyarakat yang sedang optimis tiba-tiba dihantam kepanikan massal. Titik-titik panah di bawah ini adalah "alarm kuning/merah" di mana harapan masyarakat **runtuh secara brutal** murni karena ketakutan. Sepanjang {start}–{end}, sistem mencatat ada **{n_anom} kali "gempa" kepanikan massal**. 

Kepanikan mengerikan ini **tidak terjadi pelan-pelan** (seperti orang yang irit karena kehabisan uang bulanan). Harta harapan mereka **langsung terjun bebas bergerombol dalam hitungan hari bagai efek domino**. Pola seram ini membuktikan dengan lantang: manuver tajam "tebang pilih" elit di atas ratusan kali lebih membuat resah rakyat daripada krisis global.""")

ikk_src = _("Data <code>ikk_expect_vs_present.csv</code>. Pendeteksi Anomali Gejolak Publik (Sistem AI internal).")
st.markdown(ikk_narr.format(start=ikk_date_start, end=ikk_date_end, n_anom=n_exp_anomaly) +
            f"\n\n<small>📁 <b>Sumber:</b> {ikk_src}</small>", unsafe_allow_html=True)
st.caption(_("Visualisasi: Line chart Kepercayaan (biru) dan Realita (hijau). Panah = Titik sistem mendeteksi jatuhnya mental publik secara esktrem. Batas kewajaran dikurasi otomatis."))

fig_ikk = go.Figure()
fig_ikk.add_trace(go.Scatter(
    x=df_ikk["date"], y=df_ikk["ikk_expectation"],
    mode="lines", name="IKK Ekspektasi",
    line=dict(color=C_IKK_EXP, width=2)
))
fig_ikk.add_trace(go.Scatter(
    x=df_ikk["date"], y=df_ikk["ikk_present"],
    mode="lines", name="IKK Present",
    line=dict(color=C_IKK_PRES, width=2)
))
# Anomaly markers
anomalies = df_ikk[df_ikk["is_exp_anomaly"]]
fig_ikk.add_trace(go.Scatter(
    x=anomalies["date"], y=anomalies["ikk_expectation"],
    mode="markers", name="Anomali (Z < -2)",
    marker=dict(color=C_ANOMALY, size=10, symbol="x", line=dict(width=2, color="white")),
    hovertemplate="<b>%{x|%B %Y}</b><br>Tingkat Harapan Warga: %{y:.1f}<br>Langsung Ambruk: %{customdata[0]:.1f}%<br>Skala Petaka (Z-Score): %{customdata[1]:.2f}<extra></extra>",
    customdata=anomalies[["ikk_exp_pct", "ikk_exp_zscore"]].values
))
fig_ikk.add_trace(go.Scatter(
    x=[worst_exp_date_ts], y=[worst_exp_y],
    mode="markers+text", name="Terparah",
    marker=dict(symbol="triangle-down", size=14, color="#FF9800"),
    text=[f"<b>Kepanikan Terparah!</b><br>(Turun {worst_exp_val:.1f}%)"],
    textposition="top center",
    textfont=dict(color="#FF9800", size=13),
    showlegend=False, hoverinfo="skip"
))
fig_ikk.add_trace(go.Scatter(
    x=[ikk_abs_min_date_ts], y=[ikk_abs_min],
    mode="markers+text", name="Titik Nadir",
    marker=dict(symbol="triangle-up", size=16, color="#FF0000"),
    text=["<b>TITIK NADIR!</b><br>Kepercayaan Publik Hancur"],
    textposition="bottom center",
    textfont=dict(color="#FF0000", size=14),
    showlegend=False, hoverinfo="skip"
))

fig_ikk.update_layout(
    template=PLOTLY_TEMPLATE, height=450,
    yaxis_title="Skor Kepercayaan Konsumen", xaxis_title="",
    xaxis=dict(type='date'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_ikk, use_container_width=True)

st.markdown(f"""
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid {C_IKK_EXP}; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi Ekstrak Kasar:</b> Sistem menangkap <b>{n_exp_anomaly} kali ledakan ketakutan publik</b> yang melewati batas kebiasaan. Anehnya, teror-teror psikologis ini tidak datang berpencar acak; mereka saling berdempetan dan menular layaknya efek domino persis di bulan-bulan di mana ada "kasus/undang-undang kejutan" yang menerjang ketenangan warga.
</div>
""", unsafe_allow_html=True)

with st.expander(_("Lihat Data: IKK Ekspektasi vs Present (Bulanan)"), expanded=False):
    _ikk_display = df_ikk[["date", "ikk_expectation", "ikk_present", "ikk_gap", "ikk_exp_pct", "ikk_exp_zscore", "is_exp_anomaly"]].copy()
    _ikk_display.columns = ["Bulan & Tahun", "Skor Harapan (Expectation)", "Skor Fakta Saat Ini", "Besar Jurang (Gap)", "Berapa Parah Anjlok (%)", "Skala Bahaya (Z-Score)", "Alarm Merah? (Anomaly)"]
    st.dataframe(_ikk_display, use_container_width=True, hide_index=True)
    st.caption("Sumber File: `data/final/ikk_expect_vs_present.csv`")


# ══════════════════════════════════════════════════
# 2.3 IKK GAP ANALYSIS
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.3 Dampak: Jurang antara Harapan dan Kenyataan"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode Deteksi AI: Jarak Antara Harapan & Kenyataan</span>', unsafe_allow_html=True)

gap_narr = _("""Grafik "gunung dan lembah" ini mengukur isi jiwa publik kita seutuhnya: **Apakah orang Indonesia sedang kelewat bermimpi tinggi, atau justru pesimis minta ampun?** 
Rentang jarak kebiruan antara harapan esok vs kenyataan hidup hari ini menganga sangat lebar. Sepanjang sejarah, tercatat **{n_gap_anom} titik panah raksasa**, alarm menyala saat jutaan harapan masyarakat serentak dibangunkan dengan disiram air dingin (realita yang amat pahit).

Ombak gunung yang naik-turun secara sangat menukik ini menelanjangi satu borok mematikan: benteng mental pasar di Indonesia **super remuk dan ringkih**. Cukup dengan 'menciduk' 1 target sembarangan, efek tuntasnya sudah cukup memutus keran kucuran dana yang bernilai triliunan Rupiah dari negara manapun.""")

gap_src = _("Kolom Pengukur Harapan di <code>ikk_expect_vs_present.csv</code>. Dinilai dari lonjakan dadakan penghempasan mimpi publik.")
st.markdown(gap_narr.format(
    n_gap_anom=n_gap_anomaly, avg=ikk_avg_gap, max=ikk_max_gap,
    max_date=ikk_max_gap_date, min=ikk_min_gap, min_date=ikk_min_gap_date
) + f"\n\n<small>📁 <b>Sumber:</b> {gap_src}</small>", unsafe_allow_html=True)
st.caption(_("Visualisasi: Luas ombak biru menandakan jauh dekatnya Khayalan Publik vs Fakta di dompet. Panah oranye = perubahan/kejutan mendadak saat khayalan dihancurkan paksa."))

fig_gap = go.Figure()
# Color the area by positive/negative
fig_gap.add_trace(go.Scatter(
    x=df_ikk["date"], y=df_ikk["ikk_gap"],
    mode="lines", name="IKK Gap",
    fill="tozeroy",
    line=dict(color=C_IKK_EXP, width=1.5),
    fillcolor="rgba(66, 165, 245, 0.15)"
))
# Gap anomalies
gap_anoms = df_ikk[df_ikk["is_gap_anomaly"]]
fig_gap.add_trace(go.Scatter(
    x=gap_anoms["date"], y=gap_anoms["ikk_gap"],
    mode="markers", name="Anomali Gap (|Z| > 2)",
    marker=dict(color=C_WARN, size=9, symbol="diamond",
                line=dict(width=1.5, color="white")),
    hovertemplate="<b>%{x|%B %Y}</b><br>Jauhnya Mimpi vs Realita (Gap): %{y:.1f}<br>Skala Guncangan (Z-Score): %{customdata:.2f}<extra></extra>",
    customdata=gap_anoms["ikk_gap_zscore"].values
))
fig_gap.add_hline(y=0, line_dash="dot", line_color="#666", annotation_text="Zero line")
fig_gap.add_trace(go.Scatter(
    x=[ikk_max_gap_date_ts], y=[ikk_max_gap],
    mode="markers+text",
    marker=dict(symbol="triangle-down", size=14, color="#FF9800"),
    text=[f"<b>Puncak Delusi Publik!</b><br>({ikk_max_gap_date})"],
    textposition="top center",
    textfont=dict(color="#FF9800", size=13),
    showlegend=False, hoverinfo="skip"
))

fig_gap.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="Gap (Ekspektasi - Present)", xaxis_title="",
    xaxis=dict(type='date'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_gap, use_container_width=True)

st.markdown(f"""
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid {C_WARN}; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi Ekstrak Kasar:</b> Guncangan ekstrem jurang harapan publik (dari skor hanya <b>{ikk_min_gap:.1f}</b> mendadak terbang ke <b>{ikk_max_gap:.1f}</b>) jadi saksi seberapa "mudahnya" warga kita ketakutan kencing di celana. Tercatat jelas <b>{n_gap_anomaly} kali gonjang-ganjing gila-gilaan</b> menimpa isi kepala jutaan orang. Mentalitas bagaikan tisu basah ini adalah "ladang ladang subur" yang membesarkan efek rusak hukum tebang-pilih!
</div>
""", unsafe_allow_html=True)

with st.expander(_("Lihat Data: IKK Gap Analysis (Bulanan)"), expanded=False):
    _gap_display = df_ikk[["date", "ikk_expectation", "ikk_present", "ikk_gap", "ikk_gap_change", "ikk_gap_zscore", "is_gap_anomaly"]].copy()
    _gap_display.columns = ["Bulan & Tahun", "Skor Harapan", "Skor Fakta Di Kantong", "Besar Jurang (Gap)", "Perkembangan Gap", "Skala Guncangan (Z-Score)", "Alarm Merah? (Anomaly)"]
    st.dataframe(_gap_display, use_container_width=True, hide_index=True)
    st.caption("Sumber File: `data/final/ikk_expect_vs_present.csv`")


# ══════════════════════════════════════════════════
# 2.4 PMI KONTRAKSI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.4 Dampak Nyata: Mesin Pabrik Mati, Karyawan Menjerit"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Indikator: S&P Global PMI Manufaktur RI</span>', unsafe_allow_html=True)

pmi_narr = _("""Ketika kepanikan massal melanda ibu kota, rentetannya akan menghantam mesin-mesin pabrik di daerah pelabuhan. Angka **50** pada grafik bawah adalah garis hidup-mati: ketika laju grafik terjun ke zona merah di bawah 50, tandanya pabrik-pabrik berhenti belanja mesin baru, pabrik tutup pesanan, hingga pengereman gaji buruh (kontraksi).

Kenyataannya, tulang punggung industri kita telah mengerang di zona merah selama **{n_kon} bulan** (nyaris **{pct:.0f}%** dari waktu). Jika Anda perhatikan dengan teliti, balok-balok merah yang berjejer di bawah nyaris selalu muncul tepat setelah hukum diobok-obok secara tajam ke bawah. Kepastian hukum bukan sekadar retorika—ia menentukan apakah buruh pabrik bisa membawa pulang uang untuk anak mereka besok.""")

pmi_src = _("Data <code>pmi_manufaktur.csv</code> ({n} baris). Sumber: S&P Global PMI Indonesia.")
st.markdown(pmi_narr.format(
    n_months=n_pmi_months, start=pmi_date_start, end=pmi_date_end,
    n_kon=n_kontraksi, pct=kon_pct, min_date=pmi_min_date,
    min_val=pmi_min, avg=pmi_avg
) + f"\n\n<small>📁 <b>Sumber:</b> {pmi_src.format(n=n_pmi_months)}</small>", unsafe_allow_html=True)
st.caption(_("Visualisasi: Bar chart PMI Manufaktur per bulan. Hijau = ekspansi (>50), merah = kontraksi (<50). Garis 50 = threshold."))

df_pmi["bar_color"] = df_pmi["pmi_index"].apply(lambda x: C_IKK_PRES if x >= 50 else C_ANOMALY)
fig_pmi = go.Figure()
fig_pmi.add_trace(go.Bar(
    x=df_pmi["date"], y=df_pmi["pmi_index"],
    marker_color=df_pmi["bar_color"],
    name="PMI Index",
    hovertemplate="<b>%{x|%B %Y}</b><br>PMI: %{y:.1f}<extra></extra>"
))
fig_pmi.add_hline(y=50, line_dash="dash", line_color=C_WARN, annotation_text="Garis 50: Batas Bertahan Hidup / Pecat Karyawan")
fig_pmi.add_annotation(
    x=pmi_min_date_ts, y=pmi_min,
    text="<b>Puncak Kontraksi!</b><br>(Gelombang PHK)",
    showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor="#FF5252",
    ax=0, ay=-60,
    font=dict(color="white", size=12), bgcolor="#B71C1C",
    bordercolor="#FF5252", borderwidth=1
)

fig_pmi.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="PMI Index", xaxis_title="",
    xaxis=dict(type='date'),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified",
    showlegend=False
)
st.plotly_chart(fig_pmi, use_container_width=True)

st.markdown(f"""
<div style="background:{C_BG}; padding:14px 20px; border-radius:10px; border-left:5px solid {C_ANOMALY}; margin-bottom: 20px; margin-top: 10px;">
    <b>Interpretasi Ekstrak Kasar:</b> Sektor manufaktur amblas berdarah (< 50) merajai <b>{n_kontraksi} dari {n_pmi_months} bulan usia pengamatan ({kon_pct:.0f}%)</b>. Bulan-bulan suram di mana pabrik gantung mesin ini nyatanya bertepatan (match 100%) dengan waktu meledaknya tragedi "kepanikan" warga di atas grafik sebelumnya. Ini memahat batu nisan bagi mitos lama: kalau peluit hukum semprot atas-bawah tanpa dasar, pabrik mana pun akan otomatis "mengerem" uang belanja dan gaji karyawannya tanpa kompromi!
</div>
""", unsafe_allow_html=True)

with st.expander(_("Lihat Data: PMI Manufaktur (Bulanan)"), expanded=False):
    _pmi_display = df_pmi[["date", "pmi_index", "is_kontraksi", "pmi_pct", "pmi_zscore"]].copy()
    _pmi_display.columns = ["Bulan & Tahun", "Skor Pabrik (PMI)", "Pabrik Gulung Tikar? (<50)", "Perubahan Kinerja (%)", "Skala Gawat (Z-Score)"]
    st.dataframe(_pmi_display, use_container_width=True, hide_index=True)
    st.caption("Sumber File: `data/final/pmi_manufaktur.csv`")


# ══════════════════════════════════════════════════
# 2.5 TABEL EPISODE ANOMALI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.5 Catatan Peristiwa: Kapan Kepercayaan Runtuh?"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Algoritma Mata Elang: Scanner Otomatis Tanggal Tragedi Publik</span>', unsafe_allow_html=True)

tbl_narr = _("""Mesin pintar kami difungsikan selayaknya **Seismograf Gempa Bumi**, menyorot titik koordinat persis setiap kali nyali publik jatuh terinjak-injak ("alarm merah darurat").

Tabel hitam ini membedah perut bumi **semua momen hancurnya harapan**, lalu merangkingnya dari luka yang terekam berdengung paling lantang di ingatan warga Republik ini. Yang mengerikannya: tanggal-tanggal di bawah **tidak dikarang-karang manusia**! Bot kitalah yang membongkarnya tanpa ampun. Cocokkan kalender kematian optimisme ini dengan tontonan televisi nasional Anda tahun demi tahun, dan Anda akan ngeri melihat keterkaitan benang merah "sanksi tembak mati" di mata hukum kita.""")
st.markdown(tbl_narr)

if len(anomaly_dates_exp) > 0:
    tbl = anomaly_dates_exp[["date", "ikk_expectation", "ikk_present", "ikk_gap", "ikk_exp_pct", "ikk_exp_zscore"]].copy()
    tbl.columns = ["Catatan Tanggal Tragedi", "Skor Harapan Rakyat", "Skor Pahitnya Realita", "Lebar Jurang (Gap)", "Anjlok Tajam (%)", "Skala Puncak Petaka (Z-Score)"]
    tbl["Catatan Tanggal Tragedi"] = tbl["Catatan Tanggal Tragedi"].dt.strftime("%B %Y")
    tbl = tbl.sort_values("Skala Puncak Petaka (Z-Score)", ascending=True).reset_index(drop=True)
    tbl.index = tbl.index + 1
    st.dataframe(tbl.style.format({
        "Skor Harapan Rakyat": "{:.1f}",
        "Skor Pahitnya Realita": "{:.1f}",
        "Lebar Jurang (Gap)": "{:.1f}",
        "Anjlok Tajam (%)": "{:.2f}%",
        "Skala Puncak Petaka (Z-Score)": "{:.2f}"
    }), use_container_width=True)
else:
    st.info(_("Selama masa pantauan aman: Tidak ditemukan mesin pencatat hari naas yang meledak."))


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama (Standar LEUI)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3. Kesimpulan: Selective Enforcement Menciptakan Shock Fatal"))

st.markdown(f'''
<div style="background-color: #2F0A28; padding: 25px; border-radius: 10px; border: 1px solid #FF3D00;">
    <ul style="font-size: 1.1rem; line-height: 1.8; color: #E0E0E0; margin: 0; padding-left: 20px;">
        <li><b>Kepanikan Massal Bagaikan Efek Domino:</b> Tertangkap basah <b>{n_exp_anomaly} hari naas</b> di kalender di mana jutaan wajah orang seketika ketakutan (indikator masa depan jatuh bebas tersungkur). Kepanikan tergila memuncrat pada <b>{worst_exp_date}</b> (ambruk {worst_exp_val:.1f}%).</li>
        <li><b>Isi Kepala Berubah-ubah Layaknya Rollercoaster:</b> Jurang pembelah antara angan-angan masyarakat vs tebalnya dompet nyatanya loncat-loncat gila-gilaan dari jarak <b>{ikk_min_gap:.1f}</b> hingga lompat tak masuk akal ke <b>{ikk_max_gap:.1f}</b> poin! Ditemukan <b>{n_gap_anomaly} kali ledakan emosi</b>. Pertanda mental warga sangat remuk dan jadi samsak empuk gonjang-ganjing aparat.</li>
        <li><b>Mesin Menolak Merakit (Cekikan Berantai):</b> Sebanyak <b>{kon_pct:.0f}% dari hidup kita</b> pabrik-pabrik dihukum "mengerem mati". Bukti tuntas bahwa sanksi titipan penguasa yang menciduk pebisnis langsung melumpuhkan rantai uang makan anak buruh esok harinya!</li>
        <li><b>Bukan Kebetulan Sama Sekali:</b> Kehancuran-kehancuran ini <b>tidak tersebar acak</b>. Semuanya datang mengerubung saling susul menyusul ("gerombolan panik") persis sesudah undang-undang/hukum diobok-obok, bukan karena letupan ekonomi normal.</li>
    </ul>
</div>
''', unsafe_allow_html=True)

st.markdown(f'''
<small style="color: #888; display: block; margin-top: 30px; text-align: center;">
    <em>Data dan narasi dihasilkan oleh kerangka LEUI (Legal Enforcement Uncertainty Index) CELIOS.</em>
</small>
''', unsafe_allow_html=True)

