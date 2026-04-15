"""
Phase 3 v4: Scrape Putusan MA — The Ultimate Anti-Cloudflare Strategy
Menggunakan curl_cffi untuk TLS Fingerprinting (impersonating Chrome 120)
agar Cloudflare tidak bisa mendeteksi bahwa ini adalah bot script Python.
"""
import sys
import os
import json
import time
import pandas as pd
from curl_cffi import requests

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://putusan3.mahkamahagung.go.id"

# Same priority queries
SEARCHES = [
    {"q": "wanprestasi kontrak", "label": "wanprestasi_kontrak"},
    {"q": "wanprestasi investasi", "label": "wanprestasi_investasi"},
    {"q": "perizinan usaha", "label": "perizinan_usaha"},
    {"q": "pencabutan izin", "label": "pencabutan_izin"},
    {"q": "penipuan investasi", "label": "penipuan_investasi"}
]

YEARS = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]

def main():
    print("=" * 70)
    print("PHASE 3 v4: Scraping Putusan MA — curl_cffi TLS Spoofing")
    print("Membypass WAF dengan impersonasi Chrome 120 (Network level)")
    print("=" * 70)
    
    # Init session dengan impersonate browser
    session = requests.Session(impersonate="chrome101", verify=False)
    
    print("\n[STEP 1] Tes koneksi & ambil token Session ke homepage...")
    try:
        resp = session.get(BASE, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Cookies didapat: {len(session.cookies)}")
        
        if "cf-browser-verification" in resp.text:
            print("  [WARN] Cloudflare JS challenge tertangkap! Impersonate tidak cukup.")
        elif resp.status_code == 200:
            print("  [OK] Berhasil masuk tanpa diblokir WAF!")
        else:
            print(f"  [ERR] Status aneh: {resp.status_code}")
    except Exception as e:
        print(f"  [FATAL] Timeout/Error saat load homepage: {e}")
        return

    print(f"\n[STEP 2] Memulai AJAX search ke backend MA...")
    
    all_records = []
    
    for search in SEARCHES:
        query = search["q"]
        label = search["label"]
        
        for tahun in YEARS:
            print(f"  [{label}] {tahun}...", end=" ", flush=True)
            page_num = 1
            max_pages = 2  # Ambil maksimal 2 page (total 20-30 data per query/tahun)
            
            while page_num <= max_pages:
                try:
                    # Endpoint AJAX untuk pencarian Putusan MA
                    ajax_url = f"{BASE}/search/index/pencarian/ajax/putusan"
                    
                    payload = {
                        "q": query,
                        "tahun": tahun,
                        "jenis_doc": "Putusan",
                        "page": page_num
                    }
                    
                    headers = {
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "Origin": BASE,
                        "Referer": f"{BASE}/search.html?q={query}"
                    }
                    
                    post_resp = session.post(ajax_url, data=payload, headers=headers, timeout=30)
                    
                    if post_resp.status_code != 200:
                        print(f"[HTTP {post_resp.status_code}]", end=" ")
                        break
                        
                    data = post_resp.json()
                    
                    if not data or "data" not in data or not data["data"]:
                        if page_num == 1:
                            print("[0 data]", end=" ")
                        break
                        
                    decisions = data["data"]
                    if page_num == 1:
                        total = data.get("total", "?")
                        print(f"[{total} total]", end=" ")
                        
                    for d in decisions:
                        rec = {
                            "query_label": label,
                            "query": query,
                            "tahun_search": tahun,
                            "nomor": d.get("nomor", ""),
                            "tanggal_musyawarah": d.get("tanggal_musyawarah", ""),
                            "tanggal_registrasi": d.get("tanggal_registrasi", ""),
                            "pengadilan": d.get("pengadilan", ""),
                            "lembaga_peradilan": d.get("lembaga_peradilan", ""),
                            "jenis_perkara": d.get("jenis_perkara", d.get("klasifikasi", "")),
                            "amar": d.get("amar", ""),
                            "status": d.get("status", "")
                        }
                        all_records.append(rec)
                        
                    page_num += 1
                    time.sleep(1) # delay sopan
                    
                except json.JSONDecodeError:
                    print("[ERR: Not JSON (CF block?)]", end=" ")
                    break
                except Exception as e:
                    print(f"[ERR: {str(e)[:30]}]", end=" ")
                    break
            
            print() # newline after year
            time.sleep(2)
            
    print(f"\n[SELESAI] Total {len(all_records)} data ditarik!")
    
    if all_records:
        df = pd.DataFrame(all_records)
        df = df.drop_duplicates(subset=["nomor"])
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "putusan_ma_v4.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[SAVED] {output_path}")
        
if __name__ == "__main__":
    main()
