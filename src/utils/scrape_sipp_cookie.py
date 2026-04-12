from __future__ import annotations
import sys
import requests
import json
import pandas as pd
import os
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def scrape_with_cookie():
    # User's provided cookies and headers to bypass CF
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cookie': 'PHPSESSID=mskatp6qaqsb6r4p8fdal76lm6; cf_clearance=MrnSo1eDOPz9dJilUfh8ErJKAiVWIMVj0r5zbNWrYr8-1775824310-1.2.1.1-tdgUDFTyQnutWo3R9OxdAJp6VvIvmv65wT.HdJXwDAjCN5WzocrAXsJDUtIM4fWc7Yn8hRg0kTUnzJFl5D885FB1XVYicr3QJlDu5tYyd9TZz_cqo3.VqVsUyMYHOdwUS7IkynJUYTJj9fOlq8rcqKpW01S54mJasVBvr_aDXKjRBrzrm5y1XCjR4bb_e30NwujDr6XAQpOcs8FlVhgwC7mkXEG1HHN8Ea1DYuyqHC4cPEX.OQEZI8xDW65TrPkHLIXgl07hYGoDLzcpQqva0F9czprSslGIGHDMGpWFHh8DqjZU.XxW7KaVBkz4RigYXpanveSIyyjstqeA_JAJHQ',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # We will query PN Negara directly for Wanprestasi. SIPP usually takes POST for Datatables or search.
    # In SIPP, the form submits to list_perkara/search, sometimes with POST data: 'q=wanprestasi' or similar.
    # We will try fetching the search page directly
    print("Mencoba menggunakan cookies dari cURL Anda untuk menembus SIPP PN Negara...")
    
    url = "https://sipp.pn-negara.go.id/list_perkara"
    try:
        # Initial request to see if we are in
        resp = requests.get(url, headers=headers, verify=False, timeout=15)
        if "reCAPTCHA" in resp.text or resp.status_code != 200:
            print(f"[GAGAL] Cookies sudah expired atau tidak valid. Status: {resp.status_code}")
            return
            
        print("[SUKSES] Berhasil menembus WAF Mahkamah Agung menggunakan Cookie Anda!")
        
        # SIPP Datatables AJAX endpoint
        ajax_url = "https://sipp.pn-negara.go.id/list_perkara/get_data" # or similar
        
        # Actually, let's just attempt to do a POST search if they use server-rendered.
        # But wait, we can just use Datatables AJAX form data
        data_post = {
            'sEcho': '1',
            'iColumns': '7',
            'sColumns': '',
            'iDisplayStart': '0',
            'iDisplayLength': '101', # The screenshot showed 101 records
            'mDataProp_0': '0',
            'mDataProp_1': '1',
            'mDataProp_2': '2',
            'mDataProp_3': '3',
            'mDataProp_4': '4',
            'sSearch': 'wanprestasi',
            'bRegex': 'false',
            'sSearch_0': '',
            'bRegex_0': 'false',
            'bSearchable_0': 'true',
        }
        
        print(f"Menarik 101 data perkara 'wanprestasi' via backend...")
        # Different courts have slight variations. 'list_perkara/search' or 'list_perkara/get_data'
        # Let's hit `/list_perkara/search` via POST as that is what standard SIPP does for search submission.
        
        search_resp = requests.post("https://sipp.pn-negara.go.id/list_perkara/search", headers=headers, data=data_post, verify=False)
        
        # Let's inspect what we got
        try:
            json_res = search_resp.json()
            if 'aaData' in json_res or 'data' in json_res:
                items = json_res.get('aaData', json_res.get('data', []))
                print(f"[OK] Menemukan {len(items)} baris data dari JSON!")
                df = pd.DataFrame(items)
                
                output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
                os.makedirs(output_dir, exist_ok=True)
                out_path = os.path.join(output_dir, "putusan_sipp_pn_negara_cookie.csv")
                df.to_csv(out_path, index=False, encoding='utf-8-sig')
                print(f"[BERHASIL] Data disimpan ke: {out_path}")
                return
        except Exception:
            pass
            
        print("Bukan JSON, mencoba parse HTML (SIPP versi lama/SSR)...")
        soup = BeautifulSoup(search_resp.text, 'html.parser')
        table = soup.find('table')
        if table:
            df = pd.read_html(str(table))[0]
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(output_dir, "putusan_sipp_pn_negara_cookie.csv")
            df.to_csv(out_path, index=False, encoding='utf-8-sig')
            print(f"[BERHASIL] Data HTML disimpan ke: {out_path}")
            print(df.head())
        else:
            print("[GAGAL] Tidak menemukan tabel di HTML. Screenshot HTML 500 chars:")
            print(search_resp.text[:500])
            
    except Exception as e:
        print(f"Error fatal: {e}")

if __name__ == "__main__":
    scrape_with_cookie()
