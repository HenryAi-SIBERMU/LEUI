import requests
import urllib3
import pandas as pd
from bs4 import BeautifulSoup
import os
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The courts that recon found open/partial
COURTS = [
    "pn-jakartautara", "pn-depok", "pn-palembang", "pn-kediri", "pn-purwokerto",
    "pn-padang", "pn-tasikmalaya", "pn-batam", "pn-binjai", "pn-bandaaceh",
    "pn-tangerang", "pn-lubukpakam", "pn-pontianak", "pn-banjarmasin", "pn-manado",
    "pn-bogor", "pn-jambi", "pn-palangkaraya", "pn-mataram", "pn-pekanbaru",
    "pn-samarinda", "pn-jayapura", "pn-ambon", "pn-kupang", "pn-balikpapan",
    "pn-cianjur", "pn-karawang", "pn-jakartatimur", "pn-majalengka", "pn-indramayu",
    "pn-sorong", "pn-blitar", "pn-sragen", "pn-tulungagung", "pn-garut",
    "pn-wonogiri", "pn-kuningan", "pn-sumedang", "pn-sampang", "pn-bukittinggi",
    "pn-sumenep", "pn-metro", "pn-subang", "pn-ternate", "pn-kotabumi",
    "pn-kisaran", "pn-payakumbuh", "pn-solok", "pn-tebingtinggi", "pn-stabat",
    "pn-tuban", "pn-klaten", "pn-jombang", "pn-mojokerto", "pn-rantauprapat",
    "pn-lamongan", "pn-gresik", "pn-sidoarjo"
]

def scrape_sipp_massal():
    MAX_PAGES_PER_COURT = 50  # ~1000 perkara per PN (sangat representatif, anti-blokir)
    
    print("=" * 60)
    print("SIPP MASSAL SCRAPER - WANPRESTASI")
    print(f"TARGET: 58 Pengadilan Negeri | LImit: {MAX_PAGES_PER_COURT} Halaman/PN")
    print("TARGET: 58 Pengadilan Negeri (Dari Recon)")
    print("=" * 60)

    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    payload = {'search_keyword': 'wanprestasi'}
    
    all_dfs = []
    success_count = 0

    for court in COURTS:
        print(f"\n🔎 Mulai Scraping -> {court}")
        court_total = 0
        offset = 0
        page = 1
        
        while True:
            print(f"\r   ⏳ Fetching Halaman {page} (Offset: {offset})...", end="", flush=True)
            
            # CodeIgniter SIPP uses offset at the end of the URL for pagination
            if offset == 0:
                url = f"https://sipp.{court}.go.id/list_perkara/search"
            else:
                url = f"https://sipp.{court}.go.id/list_perkara/search/{offset}"
                
            try:
                resp = session.post(url, headers=headers, data=payload, verify=False, timeout=15)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    table = soup.find('table')
                    if table:
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter(action='ignore', category=FutureWarning)
                            try:
                                df = pd.read_html(str(table))[0]
                            except ValueError: # No tables found
                                break
                        
                        # Stop if table is essentially empty or doesn't have the expected columns
                        if len(df) < 1:
                            break
                        # Sometimes SIPP tables return 'No data available in table' in a single cell
                        if len(df) == 1 and df.iloc[0].astype(str).str.contains('No data', case=False).any():
                            break
                            
                        if 1 in df.columns and 6 in df.columns:
                            # Membersihkan kolom
                            df_clean = df.copy()
                            df_clean.rename(columns={
                                1: 'Nomor Perkara',
                                2: 'Tanggal Daftar',
                                3: 'Klasifikasi Perkara',
                                4: 'Para Pihak',
                                5: 'Status Perkara',
                                6: 'Lama Proses'
                            }, inplace=True)
                            
                            df_clean['Pengadilan'] = court.replace('pn-', 'PN ').title().replace("-", " ")
                            all_dfs.append(df_clean)
                            court_total += len(df_clean)
                            
                            print(f"\r   ✅ Halaman {page} ditarik (+{len(df_clean)} baris) | Terkumpul: {court_total} perkara", end="", flush=True)
                            
                            # Cek Kondisi Berhenti (Habis Data atau Capai Limit Representatif)
                            if len(df_clean) < 20:
                                print(" [Mentok Data]", end="")
                                break
                            if page >= MAX_PAGES_PER_COURT:
                                print(f" [Limit {MAX_PAGES_PER_COURT} Hal Tercapai]", end="")
                                break
                                
                            offset += 20
                            page += 1
                            time.sleep(1.5) # Anti-DDoS / Rate Limit protection
                        else:
                            break # Unexpected table format
                    else:
                        break # No table on this page
                else:
                    print(f"\r   ❌ HTTP {resp.status_code} di Halaman {page}", end="", flush=True)
                    break
            except requests.exceptions.ReadTimeout:
                print(f"\r   ⚠️ TIMEOUT di Halaman {page} (Skipping...)", end="", flush=True)
                break
            except requests.exceptions.ConnectionError:
                print(f"\r   ⚠️ KONEKSI PUTUS di Halaman {page}", end="", flush=True)
                break
            except Exception as e:
                print(f"\r   ⚠️ ERROR di Halaman {page} : {str(e)[:30]}", end="", flush=True)
                break
                
        if court_total > 0:
            success_count += 1
            print(f"\n   🟢 SELESAI {court}: Berhasil merampas {court_total} perkara total!")
            
            # --- SAVE INCREMENTAL PER COURT ---
            # Parse durasi here before saving
            def _parse_durasi(durasi_str):
                if not isinstance(durasi_str, str): return 0
                if 'Bulan' in durasi_str:
                    return int(durasi_str.split('Bulan')[0].strip()) * 30
                elif 'Hari' in durasi_str:
                    return int(durasi_str.split('Hari')[0].strip())
                elif 'Min' in durasi_str:
                     return int(durasi_str.split('Min')[0].strip()) * 7
                return 0
                
            court_df = pd.concat(all_dfs[-len(all_dfs):]) if all_dfs else pd.DataFrame()
            if not court_df.empty and 'Lama Proses' in court_df.columns:
                court_df['durasi_hari'] = court_df['Lama Proses'].apply(_parse_durasi)
                court_df = court_df[(court_df['durasi_hari'] > 0) & (court_df['durasi_hari'] <= 1000)]
                
                out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, "sipp_nasional_wanprestasi_massal.csv")
                
                # Append to CSV
                is_first_write = not os.path.exists(out_path)
                court_df.to_csv(out_path, mode='a', index=False, header=is_first_write, encoding='utf-8-sig')
                print(f"   💾 Auto-Saved: {court} ditambahkan ke CSV!")
                
            # Clear memory for next court if needed, but we can keep building all_dfs or just reset it.
            # actually better to clear all_dfs to save memory since we're writing per court
            all_dfs = [] 
            
        else:
            print(f"\n   🔴 KOSONG {court}: Tidak ada data sama sekali.")
            
        time.sleep(1.5) # Wait before hitting the next court

    print(f"\n[SUKSES] Total pengadilan yang berhasil ditarik: {success_count} PN!")
    print("Semua data telah disimpan secara bertahap ke dalam CSV.")
    return None

if __name__ == "__main__":
    scrape_sipp_massal()
