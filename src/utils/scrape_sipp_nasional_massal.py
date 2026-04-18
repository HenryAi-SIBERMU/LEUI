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
    print("=" * 60)
    print("SIPP MASSAL SCRAPER - WANPRESTASI")
    print("TARGET: 58 Pengadilan Negeri (Dari Recon)")
    print("=" * 60)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    payload = {'search_keyword': 'wanprestasi'}
    
    all_dfs = []
    success_count = 0

    for court in COURTS:
        url = f"https://sipp.{court}.go.id/list_perkara/search"
        print(f"Scraping {court}...", end=" ")
        
        try:
            resp = requests.post(url, headers=headers, data=payload, verify=False, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                table = soup.find('table')
                if table:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter(action='ignore', category=FutureWarning)
                        df = pd.read_html(str(table))[0]
                    
                    if len(df) > 0 and 1 in df.columns and 6 in df.columns:
                        # Membersihkan kolom
                        df.rename(columns={
                            1: 'Nomor Perkara',
                            2: 'Tanggal Daftar',
                            3: 'Klasifikasi Perkara',
                            4: 'Para Pihak',
                            5: 'Status Perkara',
                            6: 'Lama Proses'
                        }, inplace=True)
                        
                        df['Pengadilan'] = court.replace('pn-', 'PN ').title().replace("-", " ")
                        all_dfs.append(df)
                        success_count += 1
                        print(f"[OK] Dapat {len(df)} baris")
                    else:
                        print("[NO_DATA] Tabel kosong / format beda")
                else:
                    print("[NO_TABLE] Tabel tidak ditemukan")
            else:
                print(f"[HTTP_{resp.status_code}]")
        except requests.exceptions.ReadTimeout:
            print("[TIMEOUT]")
        except requests.exceptions.ConnectionError:
            print("[CONN_ERROR]")
        except Exception as e:
            print(f"[ERROR] {str(e)[:30]}")
            
        time.sleep(1) # Be nice

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        print(f"\n[SUKSES] Total data diskrap: {len(final_df)} perkara dari {success_count} PN!")
        
        # Bersihkan & Extract Lama Proses
        def parse_durasi(durasi_str):
            if not isinstance(durasi_str, str): return 0
            if 'Bulan' in durasi_str:
                return int(durasi_str.split('Bulan')[0].strip()) * 30
            elif 'Hari' in durasi_str:
                return int(durasi_str.split('Hari')[0].strip())
            elif 'Min' in durasi_str:
                 return int(durasi_str.split('Min')[0].strip()) * 7
            return 0
            
        if 'Lama Proses' in final_df.columns:
            final_df['durasi_hari'] = final_df['Lama Proses'].apply(parse_durasi)
            # Filter anomali (durasi valid: 1-1000 hari)
            final_df = final_df[(final_df['durasi_hari'] > 0) & (final_df['durasi_hari'] <= 1000)]
            
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "sipp_nasional_wanprestasi_massal.csv")
        final_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"[SAVED] {out_path}")
        
        return final_df
    else:
        print("\n[GAGAL] Tidak ada satupun data yang berhasil ditarik.")
        return None

if __name__ == "__main__":
    scrape_sipp_massal()
