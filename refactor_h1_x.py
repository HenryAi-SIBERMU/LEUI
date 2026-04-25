import os

filepath = r"c:\Users\yooma\OneDrive\Desktop\duniahub\client\10. Celios5-LEUI\pages\3_H1_Inconsistency_Risk.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = """# ══════════════════════════════════════════════════════════
# ═══════════ LAYER X: VARIABEL HUKUM ═════════════════════
# ══════════════════════════════════════════════════════════"""
end_marker = """# ══════════════════════════════════════════════════════════
# ═══════════ LAYER Y: DAMPAK EKONOMI ═════════════════════
# ══════════════════════════════════════════════════════════"""

parts = content.split(end_marker)
part1_and_x = parts[0]
part2 = parts[1]

p1_parts = part1_and_x.split(start_marker)
part1 = p1_parts[0]
old_layer_x = p1_parts[1]

new_layer_x = """
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.subheader("⚠️ Bukti: Sistem Hukum Indonesia Sangat Membingungkan Investor")

st.markdown(f'''
<ul style="font-size: 1.1rem; line-height: 1.6; color: #E0E0E0; background-color: #261313; padding: 25px 40px; border-radius: 10px; border-left: 5px solid #FF5722;">
    <li><b>Pengadilan Sering Berubah Pikiran:</b> Mahkamah Agung membalikkan <b>{_reversal_rate:.1f}%</b> putusan pengadilan perdata yang lebih rendah. Kontrak bisnis rentan dibatalkan kapan saja.</li>
    <li><b>Aturan yang Mudah Hangus:</b> Sedikitnya <b>{_dicabut} regulasi bisnis esensial</b> (daerah/pusat) dicabut atau direvisi mendadak dalam periode ini.</li>
    <li><b>Sengketa Hukum yang Membludak:</b> Lebih dari <b>{_total_sipp:,} kasus sengketa korporasi</b> macet di pengadilan negeri seluruh Indonesia.</li>
</ul>
''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📊 Lihat Detail Analisis (Data Chart Mahkamah Agung & SIPP)", expanded=False):
"""

# Indent old_layer_x by 4 spaces
indented_old_x = ""
# remove the first old headers
lines = old_layer_x.strip().split("\n")
# skip first 4 lines of old headers
for line in lines[4:]:
    indented_old_x += "    " + line + "\n"

final_x = new_layer_x + "\n" + indented_old_x + "\n"

# Rewrite
with open(filepath, "w", encoding="utf-8") as f:
    f.write(part1 + start_marker + final_x + "\n" + end_marker + part2)

print("Layer X refactored successfully.")
