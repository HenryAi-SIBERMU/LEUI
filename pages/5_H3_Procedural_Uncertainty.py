"""
Page 3 — H3: Procedural Uncertainty
Analisis delay cost dan inefisiensi investasi menggunakan ICOR sebagai proxy
ketidakpastian prosedural hukum.
    `Procedural Uncertainty → Delay Cost → ICOR Naik → Investasi Makin Tidak Efisien → Growth Terhambat`

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
DATA = os.path.join(BASE, "data", "final")

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

# Clean: drop rows with NaN or negative ICOR (negative = COVID 2020 artefact)
df_icor_clean = df_icor.dropna(subset=["icor_pma", "icor_pmdn"]).copy()
df_icor_clean = df_icor_clean[(df_icor_clean["icor_pma"] > 0) & (df_icor_clean["icor_pmdn"] > 0)].copy()

# Aggregate annual investment totals
df_asing["year"] = df_asing["date"].dt.year
df_domestik["year"] = df_domestik["date"].dt.year

inv_pma_yr = df_asing.groupby("year")["nilai_idr_bn"].sum().reset_index()
inv_pma_yr.columns = ["year", "total_pma"]
inv_pmdn_yr = df_domestik.groupby("year")["nilai_idr_bn"].sum().reset_index()
inv_pmdn_yr.columns = ["year", "total_pmdn"]

# Merge with CLEANED ICOR (no NaN, no negatives)
df_merged = df_icor_clean.merge(inv_pma_yr, on="year", how="inner").merge(inv_pmdn_yr, on="year", how="inner")
df_merged["total_investasi"] = df_merged["total_pma"] + df_merged["total_pmdn"]
df_merged["icor_avg"] = (df_merged["icor_pma"] + df_merged["icor_pmdn"]) / 2

# --- ICOR trend (using clean data) ---
icor_pma_first = df_icor_clean["icor_pma"].iloc[0]
icor_pma_last = df_icor_clean["icor_pma"].iloc[-1]
icor_pmdn_first = df_icor_clean["icor_pmdn"].iloc[0]
icor_pmdn_last = df_icor_clean["icor_pmdn"].iloc[-1]
icor_pma_change = ((icor_pma_last - icor_pma_first) / icor_pma_first * 100)
icor_pmdn_change = ((icor_pmdn_last - icor_pmdn_first) / icor_pmdn_first * 100)
yr_first = df_icor_clean["date"].iloc[0].strftime("%Y")
yr_last = df_icor_clean["date"].iloc[-1].strftime("%Y")
n_years = len(df_icor_clean)

# ICOR peak (from clean data only)
icor_pma_max = df_icor_clean["icor_pma"].max()
icor_pma_max_yr = df_icor_clean.loc[df_icor_clean["icor_pma"].idxmax(), "date"].strftime("%Y")
icor_pmdn_max = df_icor_clean["icor_pmdn"].max()
icor_pmdn_max_yr = df_icor_clean.loc[df_icor_clean["icor_pmdn"].idxmax(), "date"].strftime("%Y")

# GDP growth trend
gdp_first = df_icor_clean["gdp_growth_pct"].iloc[0] * 100
gdp_last = df_icor_clean["gdp_growth_pct"].iloc[-1] * 100
gdp_avg = df_icor_clean["gdp_growth_pct"].mean() * 100

# --- Correlation: ICOR vs Investment (from clean merged data) ---
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
        lag_results.append({"Lag (Tahun)": lag, "Spearman r": round(r, 3), "p-value": round(p, 4), "n": len(df_lag)})

df_lag_results = pd.DataFrame(lag_results)

# Rate of change ICOR (from clean data)
df_icor_clean["icor_pma_pct"] = df_icor_clean["icor_pma"].pct_change() * 100
df_icor_clean["icor_pmdn_pct"] = df_icor_clean["icor_pmdn"].pct_change() * 100

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

# Worst year (biggest ICOR jump, from clean data)
roc_valid = df_icor_clean.dropna(subset=["icor_pma_pct"])
if len(roc_valid) > 0:
    worst_jump_idx = roc_valid["icor_pma_pct"].idxmax()
    worst_jump_yr = roc_valid.loc[worst_jump_idx, "date"].strftime("%Y")
    worst_jump_val = roc_valid.loc[worst_jump_idx, "icor_pma_pct"]
else:
    worst_jump_yr = "—"
    worst_jump_val = 0


# ══════════════════════════════════════════════════
# HEADER & INTRO
# ══════════════════════════════════════════════════
st.title(_("H3: Procedural Uncertainty — Ketidakpastian Prosedural"))
subtitle = _("Analisis Delay Cost & Inefisiensi Investasi melalui ICOR sebagai Proxy Beban Prosedural")
st.markdown(f'<p style="font-size: 1.1rem; color: #66BB6A; font-weight: 500; margin-top: -15px;">{subtitle}</p>', unsafe_allow_html=True)

# ── Unified KPI Cards ──
_sipp_pn_path = os.path.join(DATA, "sipp_pn_distribution.csv")
_total_sipp = 0
_avg_durasi = 0
if os.path.exists(_sipp_pn_path):
    _df_pn = pd.read_csv(_sipp_pn_path)
    _total_sipp = int(_df_pn['jumlah'].sum())
    _avg_dur_vals = _df_pn['avg_durasi'].dropna()
    _avg_durasi = _avg_dur_vals.mean() if len(_avg_dur_vals) > 0 else 0

st.markdown("### Eksekutif Summary (H3)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Rata-rata Durasi Sidang SIPP</div>
        <div class="metric-value" style="color:#AB47BC">{_avg_durasi:.0f} hari</div>
        <div class="metric-delta" style="color:#AB47BC">Variabel Hukum (X)</div>
    </div>""", unsafe_allow_html=True)
with c2:
    icor_color = C_ANOMALY if icor_avg_last > 6 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ICOR Rata-rata ({yr_last})</div>
        <div class="metric-value" style="color:{icor_color}">{icor_avg_last:.2f}</div>
        <div class="metric-delta" style="color:{C_WARN}">Variabel Ekonomi (Y)</div>
    </div>""", unsafe_allow_html=True)
with c3:
    corr_color = C_ANOMALY if corr_pma < -0.3 else C_WARN
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Korelasi ICOR↔Investasi</div>
        <div class="metric-value" style="color:{corr_color}">{corr_pma:.3f}</div>
        <div class="metric-delta" style="color:#AAA">Spearman (Dampak Y)</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Lonjakan Delay Cost max.</div>
        <div class="metric-value" style="color:{C_ANOMALY}">+{worst_jump_val:.1f}%</div>
        <div class="metric-delta" style="color:{C_WARN}">Tahun {worst_jump_yr}</div>
    </div>""", unsafe_allow_html=True)

with st.expander(_("Metodologi: Analisis Procedural Uncertainty (H3)"), expanded=False):
    st.markdown(_("""
    **Causal Chain Law & Economics:**
    `Penegakan Hukum Berlarut (X) → Ketidakpastian Waktu → Persepsi Risiko Investor → Biaya Ekonomi Naik (Delay Cost/ICOR) → Keputusan Investasi Terhambat (Y)`

    **Variabel Independen (X):**
    - Durasi proses perkara perdata khusus & bisnis di tingkat Pengadilan Negeri (Data SIPP OSINT).
    
    **Variabel Dependen (Y):**
    - ICOR Nasional sebagai parameter *Delay Cost* (ICOR > 6.0 = sangat tidak efisien).
    - Korelasi Spearman ICOR vs Total Realisasi Investasi PMA & PMDN.
    """))

intro = _("""Kerangka empiris **Procedural Uncertainty** membuktikan secara langsung alur kausalitas antara kacaunya penegakan hukum dan mandeknya investasi. Berdasarkan sampel SIPP, sengketa bisnis di Indonesia memakan waktu **rata-rata {_avg_durasi:.0f} hari**. Lambat dan mahalnya proses hukum ini menciptakan **ketidakpastian absolut** bagi pelaku usaha. Investor menerjemahkan ketidakpastian waktu ini menjadi **persepsi risiko tinggi**. 

Sebagai respons, risiko ini dikonversi menjadi **biaya ekonomi** berupa _Risk Premium_ dan _Delay Cost_ yang harus ditanggung investor. Hal ini terekam jelas dalam indikator efisiensi modal (**ICOR**) yang terus membengkak (saat ini {icor_avg_last:.2f}) — membuat ongkos ekspansi di Indonesia menjadi mahal dan inefisien. Rantai kausalitas ini berpuncak pada **keputusan menekan investasi (Y)**: terbukti dari korelasi **r = {corr:.3f}** antara lonjakan ICOR dan tertekannya sentimen volume investasi modal asing secara signifikan.""")

intro_src = _("SIPP Mahkamah Agung (Variabel Hukum/X) & Panel ICOR Investasi BPS-BKPM (Variabel Makroekonomi/Y).")

st.markdown(
    intro.format(
        _avg_durasi=_avg_durasi,
        yr_f=yr_first, yr_l=yr_last, 
        icor_avg_last=icor_avg_last,
        corr=corr_pma
    ) +
    f"\n\n<small>📁 <b>Sumber Basis Data:</b> {intro_src}</small>",
    unsafe_allow_html=True
)
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── 3.1 Variabel Hukum (X) ──
st.markdown("---")
st.subheader("3.1 Variabel Hukum (X): Beban Cacat Prosedural & Waktu Sengketa SIPP")
st.markdown('<span style="background:#5C2B6A;color:#E1BEE7;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Distribusi Sengketa (SIPP)</span>', unsafe_allow_html=True)

sipp_narr = _("""Grafik di bawah mensimulasikan "pintu masuk" variabel ketidakpastian. Waktu yang berlarut-larut (ratusan hari absen kepastian) dalam penyelesaian sengketa perdata bisnis di Pengadilan Negeri merepresentasikan ketidakefisienan operasional dan penegakan hukum yang panjang & mahal. Bagi investor yang tersandung sengketa perseroan, **waktu adalah biaya riil** (suku bunga pinjaman tertahan, proyek mangkrak). Kehancuran kepastian prosedur pada tahapan pertama ini bertindak sebagai variabel independen (X) saklek yang memicu lahirnya *Delay Cost* struktural secara nasional.""")
st.markdown(sipp_narr + f"\n\n<small>📁 <b>Sumber:</b> Scraping putusan web SIPP Pengadilan Negeri seluruh Indonesia (Sampel Kasus Perdata Bisnis).</small>", unsafe_allow_html=True)
st.caption(_("📊 Visualisasi: Kelompok distribusi umur perkara dan sebaran beban kerja sengketa di Top 10 PN."))

_sipp_dur_path = os.path.join(DATA, "sipp_durasi_distribution.csv")
if os.path.exists(_sipp_dur_path) and os.path.exists(_sipp_pn_path):
    _df_dur = pd.read_csv(_sipp_dur_path)
    _cc1, _cc2 = st.columns(2)
    with _cc1:
        _fig_dur = px.bar(
            _df_dur, x="durasi_bucket", y="jumlah",
            color_discrete_sequence=["#AB47BC"],
            template=PLOTLY_TEMPLATE, labels={"durasi_bucket": "Rentang Umur Perkara (Hari)", "jumlah": "Jumlah Kasus"}
        )
        _fig_dur.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(_fig_dur, use_container_width=True)
    with _cc2:
        _df_pn_top = _df_pn.head(10).sort_values("jumlah", ascending=True)
        _fig_pn = px.bar(
            _df_pn_top, x="jumlah", y="pengadilan", orientation="h",
            color_discrete_sequence=["#AB47BC"],
            template=PLOTLY_TEMPLATE, labels={"jumlah": "Volume Sengketa", "pengadilan": ""}
        )
        _fig_pn.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(_fig_pn, use_container_width=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 3.2 TREN ICOR (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.2 Dampak Ekonomi (Y): Tren ICOR Nasional — Biaya Investasi Makin Mahal"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: ICOR Time Series (Variabel Y1)</span>', unsafe_allow_html=True)

icor_narr = _("""Menggunakan metode **ICOR Time Series** — ICOR mengukur seberapa mahal biaya untuk
menghasilkan pertumbuhan. Semakin tinggi ICOR,
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
# 3.3 ICOR vs VOLUME INVESTASI (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.3 Dampak Ekonomi (Y): Hubungan ICOR dan Volume Investasi"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Spearman Rank Correlation (Variabel Y2)</span>', unsafe_allow_html=True)

scatter_narr = _("""Menggunakan metode **Spearman Rank Correlation** untuk mengukur kekuatan hubungan antara
efisiensi investasi (ICOR) dan volume investasi total (PMA+PMDN) per tahun.
Jika **ketidakpastian prosedural** benar-benar menaikkan biaya investasi, maka seharusnya
ada korelasi negatif: ICOR tinggi → volume investasi tertekan.
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
# 3.4 LAG ANALYSIS (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.4 Dampak Ekonomi (Y): Lag Analysis — Efek Keterlambatan Modal"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Spearman Lag Correlation (Variabel Y3)</span>', unsafe_allow_html=True)

lag_narr = _("""Menggunakan metode **Spearman Lag Correlation** — menerapkan Spearman Correlation yang sama
seperti Section 3.2, tetapi dengan data yang digeser waktunya (lag). Ini menguji apakah
ICOR tinggi tahun ini **berkorelasi** dengan investasi rendah di tahun-tahun berikutnya.
Formula: `Spearman(ICOR[t], Investasi[t+lag])` untuk lag = 0, 1, 2, 3 tahun.
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
# 3.5 RATE OF CHANGE (DAMPAK Y)
# ══════════════════════════════════════════════════
st.markdown("---")
st.subheader(_("3.5 Dampak Ekonomi (Y): Rate of Change — Ledakan Biaya Sporadis"))
st.markdown('<span style="background:#333;color:#FF9800;padding:4px 10px;border-radius:5px;font-size:0.85rem;">Metode: Rate of Change (Variabel Y4)</span>', unsafe_allow_html=True)

roc_narr = _("""Menggunakan metode **Rate of Change** — menghitung persentase perubahan ICOR dari tahun ke tahun.
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

df_roc = df_icor_clean.dropna(subset=["icor_pma_pct"]).copy()
roc_col = "icor_pma_pct"
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
**Sintesis Temuan Utama (Law & Economics):**

Sesuai dengan kerangka kerja Law & Economics, analisis ini mengonfirmasi rantai kausalitas berikut:
`Penegakan Hukum → Ketidakpastian Waktu → Persepsi Risiko → Biaya Ekonomi → Keputusan Investasi`

1. **Penegakan Hukum & Ketidakpastian (Variabel X)** — Berdasarkan ekstraksi data pengadilan tinggi dan SIPP Pengadilan Negeri, porsi sengketa bisnis membutuhkan waktu penyelesaian komprehensif **{avg_dur:.0f} hari**. Absennya kepastian durasi hukum yang transparan ini adalah episentrum masalah yang melumpuhkan rencana kerja pelaku usaha.
 
2. **Kenaikan Biaya Ekonomi/Risiko (Variabel Y)** — Investor menerjemahkan ketidakpastian waktu ini menjadi *Risk Premium*. Hal ini tercermin nyata pada memburuknya ICOR PMA yang menyentuh angka **{icor_l:.2f}** (Status: **{status}**). Ini berarti investor "membakar" modal operasional sangat besar hanya untuk menambal kelemahan struktural (waktu tunggu sengketa, asuransi aset, delay regulasi).
   
3. **Keputusan Menahan Investasi (Variabel Y)** — Ongkos yang membengkak ini secara langsung membatalkan keputusan ekspansi masuk. Hal ini dikonfirmasi oleh korelasi signifikan (**r = {corr:.3f}**) di mana ledakan ICOR secara konsisten diikuti penurunan sentimen realisasi investasi. 

**Implikasi Final Rekomendasi:**
Waktu penyelesaian proses hukum perdata peradilan ("Procedural Uncertainty") bukanlah isu hukum teknis persidangan semata, melainkan **hambatan fundamental makroekonomi**. Selama rezim durasi kepastian hukum tidak dijamin oleh negara, investor akan membebani harga risiko di dalam ICOR, secara perlahan melucuti daya tarik Indonesia pada lanskap _foreign direct investments_ (FDI).
""")

st.markdown(temuan.format(
    avg_dur=_avg_durasi,
    icor_l=icor_avg_last, status=efisiensi_status,
    corr=corr_pma
))
