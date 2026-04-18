import requests
import pandas as pd
import json
import os

def scrape_world_bank_transparency():
    print("=" * 70)
    print("PHASE: OSINT Scraping World Bank Indicator")
    print("Target: IQ.CPA.TRAN.XQ (Transparency, accountability, and corruption)")
    print("Country: Indonesia (IDN)")
    print("=" * 70)
    
    url = "http://api.worldbank.org/v2/country/idn/indicator/IQ.CPA.TRAN.XQ?format=json&per_page=100"
    
    print(f"[INFO] Menghubungi API World Bank: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if len(data) < 2:
            print("[ERROR] Data tidak ditemukan dalam response API.")
            return
            
        records = data[1]
        
        # Simpan raw JSON
        os.makedirs("../../data/raw", exist_ok=True)
        raw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "wb_transparency_indonesia_raw.json"))
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=4)
        print(f"[SAVED RAW] {raw_path}")
        
        # Parsing ke CSV
        parsed_data = []
        for rec in records:
            if rec.get('value') is not None:
                parsed_data.append({
                    "tahun": int(rec.get('date')),
                    "skor_transparansi_korupsi": float(rec.get('value'))
                })
        
        df = pd.DataFrame(parsed_data)
        # Urutkan dari tahun terlama ke terbaru
        df = df.sort_values(by="tahun").reset_index(drop=True)
        
        os.makedirs("../../data/final", exist_ok=True)
        final_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "final", "kualitas_hukum_h2.csv"))
        df.to_csv(final_path, index=False)
        print(f"[SAVED FINAL] {final_path}")
        print("\n[PREVIEW DATA]")
        print(df.tail(10))
        print("\nOSINT Selesai. Data diverifikasi dari server World Bank.")
        
    except Exception as e:
        print(f"[ERROR] Gagal melakukan request: {e}")

if __name__ == "__main__":
    scrape_world_bank_transparency()
