"""
Phase 3 v9: Scrape Putusan Mahkamah Agung & SIPP via OSINT
Target: site:putusan3.mahkamahagung.go.id dan inurl:sipp.pn-
Bypass: Menggunakan Google Custom Search API
"""
import time
import os
import sys
import pandas as pd
import requests

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Menggunakan API Key Celios
GOOGLE_API_KEY = "AIzaSyCgfjc35Ah1eCVyF8lPLNmpBhX26i5MQrs"
GOOGLE_CSE_ID = "c369c352f440840cb"

MA_KEYWORDS = [
    '"wanprestasi" "investasi"',
    '"perizinan usaha" "batal"',
    '"pencabutan izin" "tambang"',
    '"sengketa pemegang saham" "perseroan"'
]

SIPP_KEYWORDS = [
    'inurl:sipp.pn- "wanprestasi" "investasi"',
    'inurl:sipp.pn- "perbuatan melawan hukum" "perusahaan"',
    'inurl:sipp.pn- "gugatan" "penanaman modal"'
]

def search_google_cse_api(query, max_results=20):
    results = []
    url = "https://www.googleapis.com/customsearch/v1"
    
    try:
        pages = max_results // 10
        for i in range(pages):
            start_index = (i * 10) + 1
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': query,
                'num': 10,
                'start': start_index
            }
            
            resp = requests.get(url, params=params, timeout=20)
            
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('items', [])
                if not items: break
                
                for item in items:
                    href = item.get('link', '')
                    results.append({
                        "query": query,
                        "title": item.get('title', ''),
                        "snippet": item.get('snippet', ''),
                        "url": href
                    })
            elif resp.status_code == 429:
                print("[ERR: API Quota Exceeded]", end=" ")
                break
            else:
                print(f"[ERR: {resp.status_code}]", end=" ")
                break
                
            time.sleep(1)
            
    except Exception as e:
        print(f"[ERR: {str(e)[:40]}]", end=" ")
        
    return results

def main():
    print("=" * 70)
    print("PHASE 3 v9: Scraping MA & SIPP via OSINT (Google CSE)")
    print("=" * 70)
    
    # 1. MA
    print("\n--- 1. MAHKAMAH AGUNG OSINT ---")
    ma_results = []
    for kw in MA_KEYWORDS:
        dork = f"site:putusan3.mahkamahagung.go.id {kw}"
        print(f"[DORK] {dork}", end=" ... ")
        res = search_google_cse_api(dork, max_results=30)
        print(f"Dapat {len(res)} index!")
        ma_results.extend(res)
        
    if ma_results:
        df_ma = pd.DataFrame(ma_results).drop_duplicates(subset=["url"])
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        path_ma = os.path.join(output_dir, "putusan_ma_osint.csv")
        df_ma.to_csv(path_ma, index=False, encoding="utf-8-sig")
        print(f"  [SAVED] {path_ma} ({len(df_ma)} putusan unik)")
    
    # 2. SIPP
    print("\n--- 2. SIPP OSINT ---")
    sipp_results = []
    for kw in SIPP_KEYWORDS:
        print(f"[DORK] {kw}", end=" ... ")
        res = search_google_cse_api(kw, max_results=30)
        print(f"Dapat {len(res)} perkara!")
        sipp_results.extend(res)
        
    if sipp_results:
        df_sipp = pd.DataFrame(sipp_results).drop_duplicates(subset=["url"])
        
        # Extract PN name from URL
        import re
        def get_pn_name(url):
            m = re.search(r'sipp\.(pn-[a-z0-9\-]+)\.go\.id', url)
            if m: return m.group(1).replace("pn-", "PN ").title().replace("-", " ")
            return "Unknown"
            
        df_sipp['pengadilan'] = df_sipp['url'].apply(get_pn_name)
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        path_sipp = os.path.join(output_dir, "sipp_nasional_osint.csv")
        df_sipp.to_csv(path_sipp, index=False, encoding="utf-8-sig")
        print(f"  [SAVED] {path_sipp} ({len(df_sipp)} perkara dari berbagai PN)")
        print("\n  Sebaran Pengadilan Negeri SIPP:")
        print(df_sipp['pengadilan'].value_counts().head(5).to_string())

if __name__ == "__main__":
    main()
