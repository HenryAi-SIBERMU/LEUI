"""
Phase 3 v8: Scrape Putusan Mahkamah Konstitusi
Strategy: OSINT / Search Engine Dorking Bypass
Karena main web mkri.id diproteksi Cloudflare Turnstile, kita gunakan DuckDuckGo/Google
untuk mencari index PDF langsung di subdomain s.mkri.id yang tidak diproteksi.
"""
import time
import os
import sys
import pandas as pd
from urllib.parse import quote_plus
from curl_cffi import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LEUI_KEYWORDS = [
    '"cipta kerja"', '"undang-undang nomor 11 tahun 2020"',
    '"penanaman modal"', '"investasi asing"', 
    '"ketenagakerjaan"', '"undang-undang nomor 13 tahun 2003"'
]

def search_google_cse_api(query, max_results=10):
    results = []
    # Menggunakan API Key dari project Celios sebelumnya
    GOOGLE_API_KEY = "AIzaSyCgfjc35Ah1eCVyF8lPLNmpBhX26i5MQrs"
    GOOGLE_CSE_ID = "c369c352f440840cb"
    
    url = "https://www.googleapis.com/customsearch/v1"
    
    # Custom Search API paginates 10 results per page automatically
    try:
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': min(10, max_results)
        }
        
        # We can use standard requests here because we are hitting Google API, not MKRI
        import requests as std_requests
        resp = std_requests.get(url, params=params, timeout=20)
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('items', [])
            for item in items:
                href = item.get('link', '')
                if "mkri.id" in href and ("pdf" in href.lower() or "putusan" in href.lower()):
                    results.append({
                        "query": query,
                        "title": item.get('title', 'Putusan MK'),
                        "snippet": item.get('snippet', ''),
                        "pdf_url": href
                    })
        elif resp.status_code == 429:
            print("[ERR: API Quota Exceeded]", end=" ")
        else:
            print(f"[ERR: {resp.status_code}]", end=" ")
            
    except Exception as e:
        print(f"[ERR: {str(e)[:40]}]", end=" ")
        
    return results

def main():
    print("=" * 70)
    print("PHASE 3 v8: Scraping Putusan MK (Bypass OSINT Dorking)")
    print("Mengeksploitasi direktori s.mkri.id via Google CSE API v1")
    print("=" * 70)
    
    all_decisions = []
    
    for kw in LEUI_KEYWORDS:
        # Google Dork
        dork_query = f"site:s.mkri.id putusan {kw}"
        print(f"\n[DORK] {dork_query}")
        
        print(f"  Mencari...", end=" ", flush=True)
        results = search_google_cse_api(dork_query, max_results=10)
        
        if results:
            print(f"Dapat {len(results)} PDF!")
            all_decisions.extend(results)
        else:
            print("Nihil.")
            
    if all_decisions:
        df = pd.DataFrame(all_decisions)
        
        # Ekstrak Nomor Putusan dari judul/snippet (contoh: Putusan Nomor 91/PUU-XVIII/2020)
        import re
        def extract_nomor(text):
            m = re.search(r'Nomor\s+([0-9]+/[A-Za-z\-]+/[0-9]{4})', str(text), re.IGNORECASE)
            if m: return m.group(1).upper()
            return ""
            
        df['kandidat_nomor'] = df['title'].apply(extract_nomor)
        df.loc[df['kandidat_nomor'] == "", 'kandidat_nomor'] = df['snippet'].apply(extract_nomor)
        
        before = len(df)
        df = df.drop_duplicates(subset=["pdf_url"])
        print(f"\n\n[DEDUP] {before} -> {len(df)} file PDF putusan MK unik.")
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "putusan_mk_osint.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        print(f"[SAVED] {output_path}")
        print("\nTop 5 Putusan MK (Cipta Kerja / Investasi):")
        for idx, row in df.head(5).iterrows():
            print(f"  - {row['kandidat_nomor'] or 'Unparsed'}: {row['title'][:60]}...")
    else:
        print("\n\n[FAILED] Gagal mengekstrak dari search engine.")

if __name__ == "__main__":
    main()
