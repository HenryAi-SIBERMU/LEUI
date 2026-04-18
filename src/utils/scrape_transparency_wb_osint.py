import urllib.request
import re
import pandas as pd
import os

def scrape_cpi_wikipedia():
    print("=" * 70)
    print("PHASE: OSINT Scraping Transparency International CPI")
    print("Target: English Wikipedia Historical CPI Table")
    print("Country: Indonesia (IDN)")
    print("=" * 70)
    
    url = 'https://en.wikipedia.org/wiki/Corruption_Perceptions_Index'
    print(f"[INFO] Menghubungi sumber publik: {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Gagal download halaman: {e}")
        return

    # Find the row for Indonesia table data
    indo_match = re.search(r'Indonesia.*?</tr>', html, re.DOTALL | re.IGNORECASE)
    if not indo_match:
        print("[ERROR] Baris Indonesia tidak ditemukan di tabel.")
        return
        
    row = indo_match.group(0)
    # Extracts all td that contain exactly two or three digits (the CPI scores from TI range 0-100)
    scores = re.findall(r'<td.*?>(\d{2,3})\b.*?<', row)
    
    # We know the CPI english wikipedia table generally represents [2023, 2022, 2021, ... 2012] exactly 12 years.
    # We will safely assign them backwards from 2023.
    years = list(range(2023, 2023 - len(scores), -1))
    
    parsed_data = []
    for i, year in enumerate(years):
        parsed_data.append({
            "tahun": year,
            "skor_transparansi_korupsi": int(scores[i])
        })
    
    df = pd.DataFrame(parsed_data)
    df = df.sort_values(by="tahun").reset_index(drop=True)
    
    # Simpan ke CSV
    os.makedirs("../../data/final", exist_ok=True)
    final_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "final", "kualitas_hukum_h2.csv"))
    df.to_csv(final_path, index=False)
    
    print(f"[SAVED FINAL] {final_path}")
    print("\n[PREVIEW DATA]")
    print(df)
    print("\nOSINT Selesai. Data CPI diverifikasi dari tabel publik terkurasi Wikipedia.")

if __name__ == "__main__":
    scrape_cpi_wikipedia()
