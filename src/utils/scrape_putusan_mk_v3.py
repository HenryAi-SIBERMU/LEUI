"""
Phase 3 v7: Scrape Putusan Mahkamah Konstitusi (mkri.id)
Target: Judicial Review (PUU) terkait UU Ekonomi & Bisnis
Strategy: curl_cffi (TLS Spoofing) untuk pass Turnstile
"""
import pandas as pd
import time
import os
import sys
from bs4 import BeautifulSoup
from curl_cffi import requests

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "https://mkri.id/index.php"

LEUI_KEYWORDS = [
    "investasi", "penanaman modal", "cipta kerja", 
    "pertambangan", "kehutanan", "ketenagakerjaan",
    "perizinan", "pajak", "kepailitan", "perseroan"
]

def scrape_mk_keyword_curl(session, keyword, max_pages=3):
    records = []
    
    for page_num in range(1, max_pages + 1):
        print(f"  Page {page_num}...", end=" ", flush=True)
        url = f"{BASE_URL}?page=web.Putusan&id=&kat=1&cari={keyword}&hlm={page_num}"
        
        try:
            # Menggunakan curl_cffi session
            resp = session.get(url, timeout=30)
            
            if resp.status_code != 200:
                print(f"[ERR:{resp.status_code}]", end=" ")
                break
                
            if "Just a moment..." in resp.text or "cf-browser-verification" in resp.text:
                 print("[CF-Blocked]", end=" ")
                 break

            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Find the results table
            rows = soup.select("table.table tbody tr")
            if not rows or len(rows) == 0:
                print("[End of results]")
                break
                
            new_recs = 0
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    nomor = cells[0].text.strip()
                    perihal = cells[1].text.strip()
                    tanggal = cells[2].text.strip()
                    
                    pdf_link = ""
                    for a in cells[1].find_all('a'):
                        if 'href' in a.attrs and '.pdf' in a['href']:
                            pdf_link = "https://mkri.id" + a['href'] if a['href'].startswith('/') else a['href']
                            break
                            
                    records.append({
                        "query": keyword,
                        "nomor_putusan": nomor,
                        "perihal": perihal,
                        "tanggal_dibacakan": tanggal,
                        "pdf_url": pdf_link
                    })
                    new_recs += 1
            
            print(f"({new_recs} items)")
            if new_recs == 0:
                break
                
            time.sleep(1.5)
            
        except Exception as e:
            print(f"[EXCEPTION: {str(e)[:50]}]")
            break
            
    return records


def main():
    print("=" * 70)
    print("PHASE 3 v7: Scraping Putusan Mahkamah Konstitusi (mkri.id)")
    print("Strategy: curl_cffi TLS Spoofing Chrome 101")
    print("=" * 70)
    
    # Init spoofing session, nonaktifkan cert verify seperti kasus MA sebelumnya
    session = requests.Session(impersonate="chrome101", verify=False)
    
    print("[STEP 1] Testing MKRI connection...")
    try:
        resp = session.get("https://mkri.id/", timeout=30)
        print(f"  Status: {resp.status_code}")
        
        if "Just a moment..." in resp.text:
            print("  [WARN] Cloudflare Turnstile masih aktif. Spoofing gagal.")
        else:
            print("  [OK] Berhasil tembus halaman utama tanpa Turnstile!")
            
    except Exception as e:
        print(f"  [FATAL] Gagal akses: {e}")
        return

    print("\n[STEP 2] Running searches...")
    all_decisions = []
    
    for kw in LEUI_KEYWORDS:
        print(f"\n[SEARCH] '{kw}'")
        results = scrape_mk_keyword_curl(session, kw, max_pages=3)
        if results:
            all_decisions.extend(results)
            
    if all_decisions:
        df = pd.DataFrame(all_decisions)
        
        before = len(df)
        df = df.drop_duplicates(subset=["nomor_putusan"])
        print(f"\n\n[DEDUP] {before} -> {len(df)} putusan MK unik yang relevan.")
        
        def extract_year(date_str):
            try:
                parts = date_str.split()
                if len(parts) >= 3: return parts[-1]
            except: pass
            return ""
            
        df["tahun"] = df["tanggal_dibacakan"].apply(extract_year)
        
        def extract_uu(text):
            import re
            m = re.search(r'(UU|Undang-Undang)\s+(No\.|Nomor)?\s*(\d+[A-Za-z\s-]*\s+Tahun\s+\d{4})', text, re.IGNORECASE)
            if m: return m.group(3).strip()
            return ""
            
        df["uu_teruji"] = df["perihal"].apply(extract_uu)
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "putusan_mk_judicial_review.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        print(f"[SAVED] {output_path}")
        
    else:
        print("\n\n[FAILED] Tidak ada data. WAF MKRI masih menetapkan blokir.")


if __name__ == "__main__":
    main()
