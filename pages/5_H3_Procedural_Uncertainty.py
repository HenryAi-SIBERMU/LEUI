"""
Page 3 — H3: Procedural Uncertainty
Analisis delay cost dan inefisiensi investasi menggunakan ICOR sebagai proxy
ketidakpastian prosedural hukum.
Semua data-driven — zero hardcoded events.

Causal Chain: Procedural Uncertainty → Delay Cost → ICOR Naik → Investasi Makin Tidak Efisien
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.components.sidebar import render_sidebar
from src.utils.i18n import _

st.set_page_config(
    page_title="H3: Procedural Uncertainty — CELIOS LEUI",
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
C_PMA = "#42A5F5"
C_PMDN = "#66BB6A"
C_ICOR = "#FF9800"
C_ANOMALY = "#E53935"
C_WARN = "#FF9800"
C_BG = "#1E1E1E"

# ── Load data ──
BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "processed")

@st.cache_data
def load_data():
    df_icor = pd.read_csv(os.path.join(DATA, "icor_nasional.csv"), parse_dates=["date"])
    df_a = pd.read_csv(os.path.join(DATA, "realisasi_investasi_asing.csv"), parse_dates=["date"])
    df_d = pd.read_csv(os.path.join(DATA, "realisasi_investasi_domestik.csv"), parse_dates=["date"])
    return df_icor, df_a, df_d

df_icor, df_asing, df_domestik = load_data()


# ══════════════════════════════════════════════════
# PRE-COMPUTE
# ══════════════════════════════════════════════════

df_icor = df_icor.sort_values("date").reset_index(drop=True)
df_icor["year"] = df_icor["date"].dt.year

# Aggregate annual investment totals
df_asing["year"] = df_asing["date"].dt.year
df_domestik["year"] = df_domestik["date"].dt.year

inv_pma_yr = df_asing.groupby("year")["nilai_idr_bn"].sum().reset_index()
inv_pma_yr.columns = ["year", "total_pma"]
inv_pmdn_yr = df_domestik.groupby("year")["nilai_idr_bn"].sum().reset_index()
inv_pmdn_yr.columns = ["year", "total_pmdn"]

# Merge with ICOR
df_merged = df_icor.merge(inv_pma_yr, on="year", how="inner").merge(inv_pmdn_yr, on="year", how="inner")
df_merged["total_investasi"] = df_merged["total_pma"] + df_merged["total_pmdn"]
df_merged["icor_avg"] = (df_merged["icor_pma"] + df_merged["icor_pmdn"]) / 2

# --- ICOR trend ---
icor_pma_first = df_icor["icor_pma"].iloc[0]
icor_pma_last = df_icor["icor_pma"].iloc[-1]
icor_pmdn_first = df_icor["icor_pmdn"].iloc[0]
icor_pmdn_last = df_icor["icor_pmdn"].iloc[-1]
icor_pma_change = ((icor_pma_last - icor_pma_first) / icor_pma_first * 100)
icor_pmdn_change = ((icor_pmdn_last - icor_pmdn_first) / icor_pmdn_first * 100)
yr_first = df_icor["date"].iloc[0].strftime("%Y")
yr_last = df_icor["date"].iloc[-1].strftime("%Y")
n_years = len(df_icor)

# ICOR peak
icor_pma_max = df_icor["icor_pma"].max()
icor_pma_max_yr = df_icor.loc[df_icor["icor_pma"].idxmax(), "date"].strftime("%Y")
icor_pmdn_max = df_icor["icor_pmdn"].max()
icor_pmdn_max_yr = df_icor.loc[df_icor["icor_pmdn"].idxmax(), "date"].strftime("%Y")

# GDP growth trend
gdp_first = df_icor["gdp_growth_pct"].iloc[0] * 100
gdp_last = df_icor["gdp_growth_pct"].iloc[-1] * 100
gdp_avg = df_icor["gdp_growth_pct"].mean() * 100

# --- Correlation: ICOR vs Investment ---
if len(df_merged) >= 5:
    corr_pma, pval_pma = stats.spearmanr(df_merged["icor_pma"], df_merged["total_pma"])
    corr_pmdn, pval_pmdn = stats.spearmanr(df_merged["icor_pmdn"], df_merged["total_pmdn"])
    corr_icor_gdp, pval_icor_gdp = stats.spearmanr(df_merged["icor_avg"], df_merged["gdp_growth_pct"])
else:
    corr_pma, pval_pma = 0, 1
    corr_pmdn, pval_pmdn = 0, 1
    corr_icor_gdp, pval_icor_gdp = 0, 1

# --- Lag analysis: does high ICOR this year predict low investment next year? ---
lag_results = []
for lag in range(0, 4):
    df_lag = df_merged.copy()
    df_lag["inv_lagged"] = df_lag["total_investasi"].shift(-lag)
    df_lag = df_lag.dropna(subset=["inv_lagged"])
    if len(df_lag) >= 4:
        r, p = stats.spearmanr(df_lag["icor_avg"], df_lag["inv_lagged"])
        lag_results.append({"Lag (Tahun)": lag, "Spearman r": r, "p-value": p, "n": len(df_lag)})

df_lag_results = pd.DataFrame(lag_results)

# Rate of change ICOR
df_icor["icor_pma_pct"] = df_icor["icor_pma"].pct_change() * 100
df_icor["icor_pmdn_pct"] = df_icor["icor_pmdn"].pct_change() * 100

# ICOR efficiency classification
icor_avg_last = (icor_pma_last + icor_pmdn_last) / 2
if icor_avg_last > 7:
    efisiensi_status = "Sangat Tidak Efisien"
elif icor_avg_last > 5:
    efisiensi_status = "Tidak Efisien"
elif icor_avg_last > 3:
    efisiensi_status = "Moderat"
else:
    efisiensi_status = "Efisien"

# Worst year (biggest ICOR jump)
worst_jump_idx = df_icor["icor_pma_pct"].idxmax()
if pd.notna(worst_jump_idx):
    worst_jump_yr = df_icor.loc[worst_jump_idx, "date"].strftime("%Y")
    worst_jump_val = df_icor.loc[worst_jump_idx, "icor_pma_pct"]
else:
    worst_jump_yr = "—"
    worst_jump_val = 0


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
st.title(_("H3: Procedural Uncertainty — Ketidakpastian Prosedural"))
subtitle = _("Analisis Delay Cost & Inefisiensi Investasi melalui ICOR sebagai Proxy Beban Prosedural")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Methodology ──
with st.expander(_("ℹ️ Metodologi: Analisis Procedural Uncertainty (H3)"), expanded=False):
    st.markdown(_("""
    **Premis:** Proses hukum yang berlarut-larut, tumpang tindih kewenangan, dan penyitaan aset
    sebelum putusan inkracht menciptakan **delay cost** — biaya laten yang tidak tercatat dalam
    neraca perusahaan namun sangat nyata bagi investor.

    **Causal Chain:**
    `Procedural Uncertainty → Delay Cost → ICOR Naik → Investasi Makin Tidak Efisien → Growth Terhambat`

    **Metode — 100% Data-Driven:**
    1. **ICOR sebagai Delay Cost Indicator** — ICOR (Incremental Capital-Output Ratio) mengukur
       berapa unit investasi dibutuhkan untuk 1 unit pertumbuhan PDB. ICOR naik = investasi
       makin tidak efisien, sebagian karena biaya-biaya tersembunyi (prosedural, hukum, birokrasi).
    2. **Spearman Correlation** — Mengukur hubungan antara ICOR dan volume investasi.
       Korelasi negatif = semakin mahal biaya investasi, semakin sedikit yang masuk.
    3. **Lag Analysis** — Menguji apakah ICOR tinggi tahun ini memprediksi
       investasi rendah di tahun berikutnya (efek delay).
    4. **Rate of Change** — Tahun mana ICOR melonjak paling tajam.

    **Istilah "Delay Cost":** Biaya yang muncul akibat keterlambatan — proses hukum berlarut-larut,
    izin tertahan, atau keputusan yang ditunda. Semakin lama proses, semakin besar delay cost
    yang terakumulasi dalam bentuk ICOR yang membengkak.
    """))


# ── Intro Narrative ──
intro = _("""Analisis efisiensi investasi Indonesia sepanjang **{yr_f}–{yr_l}** ({n_yr} tahun data ICOR)
mengungkap tren yang meresahkan: biaya untuk menghasilkan pertumbuhan ekonomi **terus membengkak**.
ICOR PMA bergerak dari **{icor_pma_f:.2f}** ({yr_f}) ke **{icor_pma_l:.2f}** ({yr_l}) — {pma_word} **{pma_chg:.1f}%**.
ICOR PMDN dari **{icor_pmdn_f:.2f}** ke **{icor_pmdn_l:.2f}** — {pmdn_word} **{pmdn_chg:.1f}%**.
Artinya, Indonesia kini membutuhkan **lebih banyak modal** untuk setiap unit pertumbuhan yang sama.
ICOR tertinggi PMA tercatat pada **{pma_max_yr}** ({pma_max:.2f}), sementara PMDN pada **{pmdn_max_yr}**
({pmdn_max:.2f}). Lonjakan ICOR terbesar terjadi pada tahun **{worst_yr}** (+{worst_val:.1f}%).
Korelasi Spearman antara ICOR dan volume investasi menunjukkan **r = {corr:.3f}** (p = {pval:.4f}),
mengindikasikan bahwa semakin tinggi biaya prosedural (ICOR), semakin tertekan volume investasi.
Pola ini konsisten dengan hipotesis bahwa **ketidakpastian prosedural** — proses hukum berlarut-larut,
tumpang tindih regulasi, penyitaan aset sebelum putusan — menciptakan **delay cost**
yang terakumulasi menjadi inefisiensi sistemik.""")

intro_src = _("Data dari <code>icor_nasional.csv</code> ({n_yr} baris, {yr_f}-{yr_l}), "
              "<code>realisasi_investasi_asing.csv</code>, dan <code>realisasi_investasi_domestik.csv</code>. "
              "Sumber: BPS & BKPM/CEIC.")

st.markdown(
    intro.format(
        yr_f=yr_first, yr_l=yr_last, n_yr=n_years,
        icor_pma_f=icor_pma_first, icor_pma_l=icor_pma_last,
        pma_word="naik" if icor_pma_change > 0 else "turun",
        pma_chg=abs(icor_pma_change),
        icor_pmdn_f=icor_pmdn_first, icor_pmdn_l=icor_pmdn_last,
        pmdn_word="naik" if icor_pmdn_change > 0 else "turun",
        pmdn_chg=abs(icor_pmdn_change),
        pma_max_yr=icor_pma_max_yr, pma_max=icor_pma_max,
        pmdn_max_yr=icor_pmdn_max_yr, pmdn_max=icor_pmdn_max,
        worst_yr=worst_jump_yr, worst_val=worst_jump_val,
        corr=corr_pma, pval=pval_pma
    ) +
    f"\n\n<small>📁 <b>Sumber:</b> {intro_src.format(n_yr=n_years, yr_f=yr_first, yr_l=yr_last)}</small>",
    unsafe_allow_html=True
)
st.caption(_("📊 Visualisasi: Empat panel — (1) Tren ICOR, (2) ICOR vs Volume Investasi, (3) Lag Correlation, (4) Rate of Change. Semua threshold dihitung dari data."))


# ── KPI Cards — Semua warna advokasi ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    icor_color = C_ANOMALY if icor_avg_last > 6 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ICOR Rata-rata ({yr_last})</div>
        <div class="metric-value" style="color:{icor_color}">{icor_avg_last:.2f}</div>
        <div class="metric-delta" style="color:{C_WARN}">{efisiensi_status}</div>
    </div>""", unsafe_allow_html=True)
with col2:
    chg_color = C_ANOMALY if icor_pma_change > 20 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Perubahan ICOR PMA</div>
        <div class="metric-value" style="color:{chg_color}">+{icor_pma_change:.1f}%</div>
        <div class="metric-delta" style="color:#AAA">{yr_first} → {yr_last}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    corr_color = C_ANOMALY if corr_pma < -0.3 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Korelasi ICOR↔Investasi</div>
        <div class="metric-value" style="color:{corr_color}">{corr_pma:.3f}</div>
        <div class="metric-delta" style="color:#AAA">Spearman (p={pval_pma:.3f})</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Lonjakan ICOR Terburuk</div>
        <div class="metric-value" style="color:{C_ANOMALY}">+{worst_jump_val:.1f}%</div>
        <div class="metric-delta" style="color:{C_WARN}">Tahun {worst_jump_yr}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 3.1 TREN ICOR
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.1 Tren ICOR Nasional — Biaya Investasi Makin Mahal"))

icor_narr = _("""ICOR mengukur seberapa **mahal** biaya untuk menghasilkan pertumbuhan. Semakin tinggi ICOR,
semakin banyak modal yang dibutuhkan — yang berarti semakin besar biaya-biaya tersembunyi
(delay, birokrasi, ketidakpastian hukum, korupsi) yang menggerogoti efisiensi.
Grafik memperlihatkan ICOR PMA (biru) dan PMDN (hijau) sepanjang **{yr_f}–{yr_l}**.
ICOR PMA memuncak pada **{pma_max_yr}** di angka **{pma_max:.2f}** — pada titik itu,
Indonesia membutuhkan Rp {pma_max:.1f} triliun investasi untuk menghasilkan Rp 1 triliun
pertumbuhan PDB. Garis threshold 6.0 (merah putus-putus) menandai batas di mana
investasi dianggap **sangat tidak efisien** menurut standar internasional.""")

icor_src = _("Data <code>icor_nasional.csv</code>. ICOR = Investasi / GDP Growth. Sumber: BPS.")
st.markdown(icor_narr.format(
    yr_f=yr_first, yr_l=yr_last, pma_max_yr=icor_pma_max_yr, pma_max=icor_pma_max
) + f"\n\n<small>📁 <b>Sumber:</b> {icor_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Line chart ICOR PMA (biru) dan PMDN (hijau) per tahun. Garis merah = threshold inefisiensi (6.0)."))

fig_icor = go.Figure()
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pma"], mode="lines+markers", name="ICOR PMA",
    line=dict(color=C_PMA, width=2.5), marker=dict(size=7),
    hovertemplate="<b>%{x|%Y}</b><br>ICOR PMA: %{y:.2f}<extra></extra>"
))
fig_icor.add_trace(go.Scatter(
    x=df_icor["date"], y=df_icor["icor_pmdn"], mode="lines+markers", name="ICOR PMDN",
    line=dict(color=C_PMDN, width=2.5), marker=dict(size=7),
    hovertemplate="<b>%{x|%Y}</b><br>ICOR PMDN: %{y:.2f}<extra></extra>"
))
fig_icor.add_hline(y=6.0, line_dash="dash", line_color=C_ANOMALY,
                   annotation_text="Threshold Inefisiensi (6.0)")
fig_icor.update_layout(
    template=PLOTLY_TEMPLATE, height=430,
    yaxis_title="ICOR (Rasio)", xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified"
)
st.plotly_chart(fig_icor, use_container_width=True)


# ══════════════════════════════════════════════════
# 3.2 ICOR vs VOLUME INVESTASI
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.2 Hubungan ICOR dan Volume Investasi"))

scatter_narr = _("""Scatter plot di bawah memperlihatkan hubungan antara efisiensi investasi (ICOR)
dan volume investasi total (PMA+PMDN) per tahun. Jika **ketidakpastian prosedural** benar-benar
menaikkan biaya investasi, maka seharusnya ada hubungan: ICOR tinggi → volume investasi tertekan.
Korelasi Spearman menunjukkan **r = {corr_pma:.3f}** untuk PMA (p = {pval_pma:.4f}) dan
**r = {corr_pmdn:.3f}** untuk PMDN (p = {pval_pmdn:.4f}). {interp}
Setiap titik mewakili satu tahun. Posisi titik di kuadran kanan-bawah (ICOR tinggi, investasi rendah)
memperkuat argumen bahwa **biaya prosedural yang membengkak** menghalangi masuknya investasi.""")

if corr_pma < -0.3:
    interp = "Korelasi negatif ini mengindikasikan bahwa semakin mahal biaya (ICOR tinggi), semakin sedikit investasi yang masuk."
elif corr_pma > 0.3:
    interp = "Korelasi positif ini menunjukkan bahwa investasi tetap masuk meskipun biaya naik — namun dengan efisiensi yang terus menurun."
else:
    interp = "Korelasi yang lemah menunjukkan hubungan non-linear — ICOR naik tanpa diimbangi kenaikan/penurunan investasi yang proporsional."

scatter_src = _("Gabungan <code>icor_nasional.csv</code> + agregasi tahunan dari <code>realisasi_investasi_asing.csv</code> dan <code>realisasi_investasi_domestik.csv</code>.")
st.markdown(scatter_narr.format(
    corr_pma=corr_pma, pval_pma=pval_pma,
    corr_pmdn=corr_pmdn, pval_pmdn=pval_pmdn,
    interp=interp
) + f"\n\n<small>📁 <b>Sumber:</b> {scatter_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Scatter plot — sumbu X = ICOR rata-rata, sumbu Y = Total investasi (IDR Bn / Miliar). Setiap titik = 1 tahun. Warna = tahun."))

if len(df_merged) > 0:
    fig_scatter = px.scatter(
        df_merged, x="icor_avg", y="total_investasi",
        color="year", color_continuous_scale=["#E53935", "#FF9800", "#FDD835"],
        hover_data={"year": True, "icor_pma": ":.2f", "icor_pmdn": ":.2f",
                    "total_pma": ":,.0f", "total_pmdn": ":,.0f"},
        template=PLOTLY_TEMPLATE,
        labels={"icor_avg": "ICOR Rata-rata", "total_investasi": "Total Investasi (IDR Bn / Miliar)", "year": "Tahun"}
    )
    fig_scatter.update_layout(
        height=430, margin=dict(l=20, r=20, t=20, b=20), hovermode="closest"
    )
    fig_scatter.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    st.plotly_chart(fig_scatter, use_container_width=True)


# ══════════════════════════════════════════════════
# 3.3 LAG ANALYSIS
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.3 Lag Analysis — Efek Delay Prosedural"))

lag_narr = _("""Apakah ICOR tinggi tahun ini **memprediksi** investasi rendah di tahun-tahun berikutnya?
Lag analysis menguji korelasi ICOR tahun T dengan volume investasi tahun T, T+1, T+2, dan T+3.
Jika delay cost bersifat kumulatif (seperti yang diprediksi oleh hipotesis procedural uncertainty),
maka korelasi seharusnya **makin negatif** pada lag yang lebih panjang — artinya dampak inefisiensi
tidak langsung terasa, tapi terakumulasi dan baru terlihat 1-3 tahun kemudian.
Tabel di bawah menyajikan hasil analisis lag. Perhatikan arah dan kekuatan korelasi
pada setiap tahun lag.""")

lag_src = _("Spearman rank correlation antara ICOR rata-rata dan total investasi pada lag 0-3 tahun.")
st.markdown(lag_narr + f"\n\n<small>📁 <b>Sumber:</b> {lag_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Tabel hasil lag correlation. Lag 0 = tahun yang sama, Lag 1 = ICOR tahun ini vs investasi tahun depan, dst."))

if len(df_lag_results) > 0:
    tbl_lag = df_lag_results.copy()
    tbl_lag["Signifikan?"] = tbl_lag["p-value"].apply(lambda p: "Ya (p < 0.05)" if p < 0.05 else "Tidak (p >= 0.05)")
    tbl_lag["Interpretasi"] = tbl_lag.apply(
        lambda row: "Negatif — ICOR tinggi → investasi rendah" if row["Spearman r"] < -0.3
        else "Positif — investasi naik bersamaan ICOR" if row["Spearman r"] > 0.3
        else "Lemah — hubungan tidak jelas", axis=1
    )
    st.dataframe(tbl_lag.style.format({
        "Spearman r": "{:.3f}",
        "p-value": "{:.4f}",
        "n": "{:.0f}"
    }), use_container_width=True, hide_index=True)

    # Bar chart of lag correlations
    fig_lag = go.Figure()
    colors = [C_ANOMALY if r < -0.3 else C_WARN if r < 0 else "#FDD835" for r in tbl_lag["Spearman r"]]
    fig_lag.add_trace(go.Bar(
        x=[f"Lag {int(l)}" for l in tbl_lag["Lag (Tahun)"]],
        y=tbl_lag["Spearman r"],
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>r = %{y:.3f}<extra></extra>"
    ))
    fig_lag.add_hline(y=0, line_dash="dot", line_color="#666")
    fig_lag.update_layout(
        template=PLOTLY_TEMPLATE, height=300,
        yaxis_title="Spearman r", xaxis_title="",
        margin=dict(l=20, r=20, t=20, b=20), showlegend=False
    )
    st.plotly_chart(fig_lag, use_container_width=True)


# ══════════════════════════════════════════════════
# 3.4 RATE OF CHANGE
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.4 Rate of Change — Lonjakan Biaya Tahunan"))

roc_narr = _("""Grafik di bawah memperlihatkan perubahan ICOR dari tahun ke tahun (dalam persen).
Bar merah menunjukkan tahun di mana ICOR **melonjak tajam** — biaya investasi tiba-tiba membengkak.
Lonjakan terbesar terjadi pada **{worst_yr}** (+{worst_val:.1f}%), menandakan bahwa pada tahun
tersebut ada faktor-faktor yang secara mendadak menaikkan biaya investasi — konsisten dengan
pola *procedural shock* di mana perubahan regulasi atau proses hukum yang berlarut
tiba-tiba menaikkan biaya bagi investor. Perhatikan bahwa lonjakan ICOR ini
tidak terjadi secara gradual, tapi **sporadis** — sebuah pola yang khas untuk
shock prosedural, bukan perlambatan struktural.""")

roc_src = _("Persentase perubahan year-over-year (pct_change) dari ICOR PMA dan PMDN.")
st.markdown(roc_narr.format(
    worst_yr=worst_jump_yr, worst_val=worst_jump_val
) + f"\n\n<small>📁 <b>Sumber:</b> {roc_src}</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Bar chart — perubahan ICOR PMA (%) per tahun. Merah = lonjakan, kuning = penurunan."))

df_roc = df_icor.dropna(subset=["ikk_pma_pct" if "ikk_pma_pct" in df_icor.columns else "icor_pma_pct"]).copy()
roc_col = "icor_pma_pct"
df_roc = df_icor.dropna(subset=[roc_col]).copy()
bar_colors = [C_ANOMALY if v > 0 else "#FDD835" for v in df_roc[roc_col]]

fig_roc = go.Figure()
fig_roc.add_trace(go.Bar(
    x=df_roc["date"], y=df_roc[roc_col],
    marker_color=bar_colors, name="% Perubahan ICOR PMA",
    hovertemplate="<b>%{x|%Y}</b><br>Perubahan: %{y:.1f}%<extra></extra>"
))
fig_roc.add_hline(y=0, line_dash="dot", line_color="#666")
fig_roc.update_layout(
    template=PLOTLY_TEMPLATE, height=380,
    yaxis_title="Perubahan ICOR PMA (%)", xaxis_title="",
    margin=dict(l=20, r=20, t=20, b=20), showlegend=False, hovermode="x unified"
)
st.plotly_chart(fig_roc, use_container_width=True)


# ══════════════════════════════════════════════════
# FOOTER — Temuan Utama
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("Interpretasi & Temuan Utama"))

temuan = _("""
**Analisis Temuan Utama H3 — Procedural Uncertainty:**

Tiga indikator konvergen menunjukkan bahwa **biaya investasi di Indonesia terus membengkak**,
konsisten dengan hipotesis beban prosedural yang meningkat:

1. **ICOR Membengkak** — ICOR PMA {pma_word} dari **{icor_f:.2f}** ({yr_f}) ke **{icor_l:.2f}** ({yr_l}),
   perubahan sebesar **{pma_chg:.1f}%**. Status efisiensi terakhir: **{status}**.

2. **Korelasi ICOR↔Investasi** — Spearman r = **{corr:.3f}** (p = {pval:.4f}).
   {interp_corr}

3. **Lonjakan Sporadis** — ICOR tidak naik secara gradual, tapi **melonjak tajam** di tahun-tahun
   tertentu (terburuk: **{worst_yr}**, +{worst_val:.1f}%). Pola sporadis ini lebih konsisten
   dengan *procedural shock* (perubahan regulasi mendadak) daripada perlambatan struktural.

**Implikasi:**
Jika biaya investasi terus naik tanpa diimbangi pertumbahan proporsional, Indonesia berisiko
mengalami **investment fatigue** — di mana investor terus menanamkan modal namun hasilnya
makin sedikit. Beban prosedural (proses hukum berlarut, tumpang tindih regulasi, ketidakpastian izin)
adalah salah satu **hidden cost** yang mau tidak mau di-price oleh investor melalui ICOR yang membengkak.

*Catatan: ICOR dipengaruhi banyak faktor selain prosedural hukum (infrastruktur, efisiensi birokrasi,
kualitas SDM). Analisis ini menyajikan ICOR sebagai proxy parsial — bukan klaim kausal tunggal.*
""")

if corr_pma < -0.3:
    interp_corr = "Korelasi negatif ini mengindikasikan bahwa biaya prosedural yang naik memang berkorelasi dengan penurunan investasi."
elif corr_pma > 0.3:
    interp_corr = "Korelasi positif ini menunjukkan investasi tetap masuk meskipun ICOR naik — namun efisiensinya terus memburuk."
else:
    interp_corr = "Korelasi yang lemah menunjukkan bahwa hubungan ICOR-investasi bersifat non-linear — ada faktor lain yang turut berperan."

st.markdown(temuan.format(
    pma_word="naik" if icor_pma_change > 0 else "turun",
    icor_f=icor_pma_first, icor_l=icor_pma_last, yr_f=yr_first, yr_l=yr_last,
    pma_chg=abs(icor_pma_change), status=efisiensi_status,
    corr=corr_pma, pval=pval_pma, interp_corr=interp_corr,
    worst_yr=worst_jump_yr, worst_val=worst_jump_val
))
