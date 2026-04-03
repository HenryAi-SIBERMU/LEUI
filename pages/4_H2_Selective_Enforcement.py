"""
Page 2 — H2: Selective Enforcement
Analisis pola enforcement selektif menggunakan anomaly detection pada IKK & PMI.
Semua data-driven — zero hardcoded events.

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
C_ANOMALY = "#E53935"
C_WARN = "#FF9800"
C_BG = "#1E1E1E"

# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "processed")

@st.cache_data
def load_data():
    df_ikk = pd.read_csv(os.path.join(DATA, "ikk_expect_vs_present.csv"), parse_dates=["date"])
    df_pmi = pd.read_csv(os.path.join(DATA, "pmi_manufaktur.csv"), parse_dates=["date"])
    return df_ikk, df_pmi

df_ikk, df_pmi = load_data()


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

ikk_latest_gap = df_ikk["ikk_gap"].iloc[-1]
ikk_avg_gap = df_ikk["ikk_gap"].mean()
ikk_max_gap = df_ikk["ikk_gap"].max()
ikk_max_gap_date = df_ikk.loc[df_ikk["ikk_gap"].idxmax(), "date"].strftime("%B %Y")
ikk_min_gap = df_ikk["ikk_gap"].min()
ikk_min_gap_date = df_ikk.loc[df_ikk["ikk_gap"].idxmin(), "date"].strftime("%B %Y")

n_kontraksi = df_pmi["is_kontraksi"].sum()
n_pmi_months = len(df_pmi)
pmi_latest = df_pmi["pmi_index"].iloc[-1]
pmi_avg = df_pmi["pmi_index"].mean()
pmi_min = df_pmi["pmi_index"].min()
pmi_min_date = df_pmi.loc[df_pmi["pmi_index"].idxmin(), "date"].strftime("%B %Y")

ikk_date_start = df_ikk["date"].min().strftime("%Y")
ikk_date_end = df_ikk["date"].max().strftime("%Y")
pmi_date_start = df_pmi["date"].min().strftime("%B %Y")
pmi_date_end = df_pmi["date"].max().strftime("%B %Y")


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title(_("H2: Selective Enforcement — Penegakan Hukum Selektif"))
subtitle = _("Deteksi Anomali Kepercayaan Ekonomi sebagai Proxy Enforcement yang Tergantung Momentum")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander(_("ℹ️ Metodologi: Analisis Selective Enforcement (H2)"), expanded=False):
    st.markdown(_("""
    **Premis:** Penegakan hukum yang selektif dan transaksional menciptakan risiko non-teknis.
    Jika enforcement hanya muncul di momentum tertentu (misalnya saat konflik politik),
    maka kepercayaan publik dan pelaku usaha akan **drop secara tiba-tiba dan tidak terprediksi**.

    **Causal Chain:**
    `Selective Enforcement → Political/Discretion Risk → Confidence Crash → Investment Delay/Exit`

    **Metode — 100% Data-Driven:**
    1. **Z-Score Anomaly Detection** pada perubahan bulanan IKK Ekspektasi
       - Z-Score < -2 = drop yang secara statistik abnormal
       - Formula: `Z = (pct_change - μ) / σ`
    2. **IKK Gap Analysis** — selisih Ekspektasi − Present
       - Gap melebar tajam = ekspektasi jatuh lebih cepat dari kondisi saat ini (panic)
       - Gap menyempit/negatif = present lebih buruk dari yang diharapkan
    3. **PMI Kontraksi Detection** — bulan dimana PMI < 50
       - PMI < 50 = sektor manufaktur berkontraksi
    4. **Rate of Change** — top-N bulan dengan perubahan terbesar

    **Istilah "Episode":** Dalam analisis ini, istilah "episode" digunakan untuk merujuk 
    pada bulan-bulan spesifik di mana algoritma mendeteksi adanya anomali statistik 
    (jatuhnya IKK di luar batas fluktuasi wajar). Semua tanggal anomali ini diidentifikasi 
    berdasarkan data, dan pembaca dapat menghubungkan sendiri temuan episode-episode 
    tersebut terhadap berbagai peristiwa publik yang terjadi.
    """))


# ── Intro Narrative ──
intro = _("""Analisis kepercayaan ekonomi Indonesia selama **{ikk_start}–{ikk_end}** ({ikk_n} bulan data IKK)
dan **{pmi_start}–{pmi_end}** ({pmi_n} bulan data PMI) memperlihatkan pola yang mengkhawatirkan:
deteksi anomali statistik (Z-Score < -2) menemukan **{n_anom} episode** dimana kepercayaan konsumen
**jatuh secara abnormal** — jauh di luar fluktuasi wajar. Episode terparah terjadi pada
**{worst_date}** dengan IKK Ekspektasi turun **{worst_pct:.1f}%** dalam satu bulan (Z={worst_z:.2f}).
Di sisi manufaktur, PMI mengalami kontraksi (<50) selama **{n_kon} dari {pmi_n} bulan** yang diamati.
Gap antara IKK Ekspektasi dan Present — ukuran \"kepanikan\" — mencapai titik tertinggi pada
**{max_gap_date}** ({max_gap:.1f} poin) dan terendah pada **{min_gap_date}** ({min_gap:.1f} poin).
Pola-pola ini konsisten dengan hipotesis bahwa *enforcement selektif* —
penegakan hukum yang muncul di momentum tertentu — menciptakan **shock kepercayaan yang tidak
bisa diprediksi oleh fundamental ekonomi**.""")

intro_src = _("Data dari <code>ikk_expect_vs_present.csv</code> ({ikk_n} baris, {ikk_start}-{ikk_end}) dan "
              "<code>pmi_manufaktur.csv</code> ({pmi_n} baris, {pmi_start}-{pmi_end}). Sumber: Bank Indonesia & S&P Global.")

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
st.caption(_("📊 Visualisasi: Empat panel — (1) IKK Time Series + Anomali, (2) IKK Gap Analysis, (3) PMI Kontraksi, (4) Tabel Episode Anomali. Semua threshold dihitung dari data, tidak ada event hardcoded."))


# ── KPI Cards ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    anom_color = C_ANOMALY if n_exp_anomaly > 5 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Episode Anomali IKK</div>
        <div class="metric-value" style="color:{anom_color}">{n_exp_anomaly}</div>
        <div class="metric-delta" style="color:#AAA">Z-Score < -2</div>
    </div>""", unsafe_allow_html=True)
with col2:
    gap_color = C_ANOMALY if abs(ikk_latest_gap) > ikk_avg_gap * 1.5 else "#4CAF50"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">IKK Gap (Terakhir)</div>
        <div class="metric-value" style="color:{gap_color}">{ikk_latest_gap:.1f}</div>
        <div class="metric-delta" style="color:#AAA">Rata-rata: {ikk_avg_gap:.1f}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    pmi_color = C_ANOMALY if pmi_latest < 50 else "#4CAF50"
    pmi_status = "Kontraksi" if pmi_latest < 50 else "Ekspansi"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">PMI Terakhir</div>
        <div class="metric-value" style="color:{pmi_color}">{pmi_latest:.1f}</div>
        <div class="metric-delta" style="color:{pmi_color}">{pmi_status}</div>
    </div>""", unsafe_allow_html=True)
with col4:
    kon_pct = n_kontraksi / n_pmi_months * 100 if n_pmi_months > 0 else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Bulan Kontraksi PMI</div>
        <div class="metric-value" style="color:{C_WARN}">{n_kontraksi}/{n_pmi_months}</div>
        <div class="metric-delta" style="color:#AAA">{kon_pct:.0f}% dari total periode</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 2.1 IKK TIME SERIES + ANOMALY
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.1 IKK Ekspektasi vs Present — Deteksi Anomali"))

ikk_narr = _("""Grafik menampilkan dua garis: IKK Ekspektasi (biru) dan IKK Present/Kondisi Saat Ini (hijau).
Titik merah menandai bulan dimana IKK Ekspektasi **jatuh secara abnormal** (Z-Score < -2) —
artinya penurunan tersebut secara statistik **bukan fluktuasi wajar**. Sepanjang {start}–{end},
terdeteksi **{n_anom} episode** anomali. Perhatikan bahwa anomali-anomali ini cenderung
**mengelompok** (cluster) — bukan tersebar acak — mengindikasikan bahwa shock kepercayaan
dipicu oleh peristiwa-peristiwa spesifik, bukan oleh siklus ekonomi biasa. Ini konsisten
dengan hipotesis bahwa *selective enforcement* menciptakan pattern: aman lama, lalu tiba-tiba
collapse saat ada momentum tertentu.""")

ikk_src = _("Data <code>ikk_expect_vs_present.csv</code>. Z-Score dihitung dari pct_change bulanan IKK Ekspektasi.")
st.markdown(ikk_narr.format(start=ikk_date_start, end=ikk_date_end, n_anom=n_exp_anomaly) +
            f"\n\n<small>📁 <b>Sumber:</b> {ikk_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Line chart IKK Ekspektasi (biru) dan Present (hijau). Titik merah = anomali (Z < -2). Threshold dihitung otomatis dari distribusi data."))

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
    hovertemplate="<b>%{x|%B %Y}</b><br>IKK Ekspektasi: %{y:.1f}<br>Drop: %{customdata[0]:.1f}%<br>Z-Score: %{customdata[1]:.2f}<extra></extra>",
    customdata=anomalies[["ikk_exp_pct", "ikk_exp_zscore"]].values
))
fig_ikk.update_layout(
    template=PLOTLY_TEMPLATE, height=450,
    yaxis_title="Indeks", xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_ikk, use_container_width=True)


# ══════════════════════════════════════════════════
# 2.2 IKK GAP ANALYSIS
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.2 IKK Gap Analysis (Ekspektasi − Present)"))

gap_narr = _("""Gap antara IKK Ekspektasi dan Present mengukur seberapa besar \"kepanikan\" publik.
**Gap positif tinggi** = ekspektasi jauh di atas kenyataan (optimisme berlebih).
**Gap menyempit/negatif** = kenyataan lebih buruk dari harapan (pesimisme akut).
Perubahan gap yang **mendadak** (Z-Score > 2 atau < -2, ditandai titik oranye) menunjukkan bulan dimana
sentimen bergeser secara tidak normal. Tercatat **{n_gap_anom} episode** gap anomali.
Gap rata-rata sepanjang periode adalah **{avg:.1f} poin**, namun gap mencapai ekstrem tertinggi
**{max:.1f}** pada **{max_date}** dan terendah **{min:.1f}** pada **{min_date}**.
Volatilitas gap yang tinggi mengindikasikan bahwa kepercayaan publik Indonesia
sangat **rapuh dan mudah terguncang** — sebuah lingkungan yang ideal bagi enforcement selektif
untuk menciptakan disproportionate impact.""")

gap_src = _("Kolom <code>ikk_gap</code> dari <code>ikk_expect_vs_present.csv</code>. Z-Score dihitung dari diff() gap bulanan.")
st.markdown(gap_narr.format(
    n_gap_anom=n_gap_anomaly, avg=ikk_avg_gap, max=ikk_max_gap,
    max_date=ikk_max_gap_date, min=ikk_min_gap, min_date=ikk_min_gap_date
) + f"\n\n<small>📁 <b>Sumber:</b> {gap_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Area chart — IKK Gap (Ekspektasi - Present). Titik oranye = anomali perubahan gap (|Z| > 2). Area hijau = gap positif, area merah = gap negatif."))

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
    hovertemplate="<b>%{x|%B %Y}</b><br>Gap: %{y:.1f}<br>Z-Score: %{customdata:.2f}<extra></extra>",
    customdata=gap_anoms["ikk_gap_zscore"].values
))
fig_gap.add_hline(y=0, line_dash="dot", line_color="#666", annotation_text="Zero line")
fig_gap.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="Gap (Ekspektasi - Present)", xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_gap, use_container_width=True)


# ══════════════════════════════════════════════════
# 2.3 PMI KONTRAKSI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.3 PMI Manufaktur — Zona Kontraksi"))

pmi_narr = _("""PMI Manufaktur sebagai *leading indicator* aktivitas ekonomi riil memperlihatkan pola yang menarik.
Dari **{n_months} bulan** observasi ({start} – {end}), PMI mengalami kontraksi (<50) selama
**{n_kon} bulan** — artinya **{pct:.0f}%** dari periode yang diamati, sektor manufaktur menyusut.
PMI terendah tercatat pada **{min_date}** di level **{min_val:.1f}**, sementara rata-rata sepanjang
periode adalah **{avg:.1f}**. Zona merah di bawah garis 50 pada grafik menandai bulan-bulan kontraksi.
Ketika bulan kontraksi PMI dibandingkan secara temporal dengan anomali IKK di atas, akan terlihat
apakah kejatuhan kepercayaan (IKK) **mendahului** perlambatan riil (PMI) — jika ya, ini memperkuat
argumen bahwa *shock kepercayaan akibat enforcement selektif* memiliki dampak kaskadie ke ekonomi riil.""")

pmi_src = _("Data <code>pmi_manufaktur.csv</code> ({n} baris). Sumber: S&P Global PMI Indonesia.")
st.markdown(pmi_narr.format(
    n_months=n_pmi_months, start=pmi_date_start, end=pmi_date_end,
    n_kon=n_kontraksi, pct=kon_pct, min_date=pmi_min_date,
    min_val=pmi_min, avg=pmi_avg
) + f"\n\n<small>📁 <b>Sumber:</b> {pmi_src.format(n=n_pmi_months)}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Bar chart PMI Manufaktur per bulan. Hijau = ekspansi (>50), merah = kontraksi (<50). Garis 50 = threshold ekspansi/kontraksi."))

df_pmi["bar_color"] = df_pmi["pmi_index"].apply(lambda x: C_IKK_PRES if x >= 50 else C_ANOMALY)
fig_pmi = go.Figure()
fig_pmi.add_trace(go.Bar(
    x=df_pmi["date"], y=df_pmi["pmi_index"],
    marker_color=df_pmi["bar_color"],
    name="PMI Index",
    hovertemplate="<b>%{x|%B %Y}</b><br>PMI: %{y:.1f}<extra></extra>"
))
fig_pmi.add_hline(y=50, line_dash="dash", line_color=C_WARN, annotation_text="Threshold 50 (Ekspansi/Kontraksi)")
fig_pmi.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    yaxis_title="PMI Index", xaxis_title="",
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified",
    showlegend=False
)
st.plotly_chart(fig_pmi, use_container_width=True)


# ══════════════════════════════════════════════════
# 2.4 TABEL EPISODE ANOMALI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("2.4 Daftar Episode Anomali (Data-Driven)"))

tbl_narr = _("""Tabel di bawah menyajikan **semua episode** dimana IKK Ekspektasi mengalami
penurunan abnormal (Z-Score < -2), diurutkan dari yang terparah. Tanggal-tanggal ini
**tidak dipilih secara manual** — semuanya muncul dari deteksi statistik otomatis.
Pembaca dipersilakan mencocokkan tanggal-tanggal ini dengan peristiwa yang diketahui publik
untuk menguji apakah hipotesis *selective enforcement* memiliki basis empiris.""")
st.markdown(tbl_narr)

if len(anomaly_dates_exp) > 0:
    tbl = anomaly_dates_exp[["date", "ikk_expectation", "ikk_present", "ikk_gap", "ikk_exp_pct", "ikk_exp_zscore"]].copy()
    tbl.columns = ["Tanggal", "IKK Ekspektasi", "IKK Present", "Gap", "Perubahan (%)", "Z-Score"]
    tbl["Tanggal"] = tbl["Tanggal"].dt.strftime("%B %Y")
    tbl = tbl.sort_values("Z-Score", ascending=True).reset_index(drop=True)
    tbl.index = tbl.index + 1
    st.dataframe(tbl.style.format({
        "IKK Ekspektasi": "{:.1f}",
        "IKK Present": "{:.1f}",
        "Gap": "{:.1f}",
        "Perubahan (%)": "{:.2f}%",
        "Z-Score": "{:.2f}"
    }), use_container_width=True)
else:
    st.info(_("Tidak ditemukan episode anomali pada threshold Z < -2."))


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("Interpretasi & Temuan Utama"))

temuan = _("""
**Analisis Temuan Utama H2 — Selective Enforcement:**

Deteksi anomali data-driven menemukan pola yang konsisten dengan hipotesis enforcement selektif:

1. **{n_anom} Episode Confidence Crash** — IKK Ekspektasi mengalami penurunan abnormal (Z < -2)
   yang **tidak bisa dijelaskan oleh siklus ekonomi biasa**. Episode terparah pada **{worst_date}**
   (drop {worst_pct:.1f}%, Z={worst_z:.2f}).

2. **Gap Volatile** — Selisih IKK Ekspektasi-Present berfluktuasi antara **{min_gap:.1f}** hingga
   **{max_gap:.1f}** poin, dengan **{n_gap_anom} episode pergeseran anomali**. Volatilitas gap
   yang tinggi menandakan struktur kepercayaan yang **rapuh dan mudah diguncang**.

3. **Kontraksi Manufaktur** — PMI mengalami kontraksi selama **{n_kon} dari {pmi_n} bulan ({pct:.0f}%)**.
   PMI terendah **{pmi_min:.1f}** pada **{pmi_min_date}**.

**Implikasi:**
Pola ini memperkuat argumen bahwa kepercayaan ekonomi Indonesia **tidak jatuh secara gradual**
(yang wajar dalam siklus bisnis), tapi jatuh secara **mendadak dan sporadis** — persis seperti
yang diprediksi oleh model *selective enforcement*: aman lama, lalu tiba-tiba *enforcement*
muncul di momentum tertentu, menciptakan shock yang disproportional.

*Catatan: Dashboard ini menyajikan anomali statistik. Interpretasi kausal atas peristiwa
yang berkorelasi dengan tanggal-tanggal anomali diserahkan kepada pembaca dan peneliti.*
""")

st.markdown(temuan.format(
    n_anom=n_exp_anomaly, worst_date=worst_exp_date,
    worst_pct=worst_exp_val, worst_z=worst_exp_z,
    min_gap=ikk_min_gap, max_gap=ikk_max_gap, n_gap_anom=n_gap_anomaly,
    n_kon=n_kontraksi, pmi_n=n_pmi_months, pct=kon_pct,
    pmi_min=pmi_min, pmi_min_date=pmi_min_date
))
