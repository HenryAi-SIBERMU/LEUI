from __future__ import annotations
import sys
import time
import os
import pandas as pd
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    print("="*60)
    print("SIPP PN JAKARTA PUSAT - PLAYWRIGHT SCRAPER")
    print("="*60)
    print("\n* Membuka browser Playwright (Headless=False)...")
    print("* JIKA MUNCUL CAPTCHA, SILAKAN SELESAIKAN SECARA MANUAL DI LAYAR ANDA.")
    
    with sync_playwright() as p:
        # Launch browser visibly so user can bypass Captcha
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        results_data = []

        # Intercept AJAX JSON responses (Cleanest way to get Datatable data)
        def handle_response(response):
            # Cek jika ini response dari pencarian datatables
            if "list_perkara" in response.url and response.request.method == "POST":
                try:
                    json_data = response.json()
                    if "data" in json_data:
                        print(f"\n[INTERCEPT] BINGO! Berhasil menangkap payload JSON: {len(json_data['data'])} baris dari {response.url}")
                        results_data.extend(json_data["data"])
                except Exception:
                    pass

        page.on("response", handle_response)
        
        print("\nMenuju portal sipp.pn-negara.go.id...")
        page.goto("https://sipp.pn-negara.go.id/list_perkara", wait_until="domcontentloaded")
        
        print("Menunggu elemen pencarian... (Sedang melewati CAPTCHA jika ada)")
        try:
            # SIPP selalu memiliki tombol "Cari" berwarna hijau atau tabel data
            page.wait_for_selector('text="Cari"', timeout=60000)
            print("[OK] Berhasil masuk ke Halaman Utama SIPP!")
        except Exception:
            print("[ERROR] Timeout. Gagal melewati Captcha atau koneksi lambat.")
            return

        print("\nMelakukan injeksi pencarian 'wanprestasi'...")
        try:
            # Cari input yang paling masuk akal (SIPP biasanya pakai datatables)
            inputs = page.query_selector_all('input')
            search_box = None
            for inp in inputs:
                # Cari input form yang kosong / bisa diisi
                tipe = inp.get_attribute('type')
                if tipe in ['text', 'search', None]:
                    search_box = inp
                    break
                    
            if search_box:
                search_box.fill("wanprestasi")
                time.sleep(1)
                
                # Klik tombol cari jika ada
                cari_btns = page.query_selector_all('text="Cari"')
                if cari_btns:
                    cari_btns[0].click()
                else:
                    page.keyboard.press("Enter")
                    
                print("Meminta data AJAX... Menunggu 10 detik.")
                time.sleep(10) # Beri waktu datatable untuk fetch AJAX POST
        except Exception as e:
            print(f"Ada kendala saat auto-search: {e}")

        df = pd.DataFrame()

        print("\nMemproses hasil...")
        if results_data:
            print(f"Total baris didapat via AJAX: {len(results_data)}")
            # SIPP returns array of arrays for datatables format
            df = pd.DataFrame(results_data)
        else:
            print("Tidak mendapat respon AJAX, menyedot via HTML DOM Extract (Fallback)...")
            html = page.content()
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                table = soup.find('table')
                if table:
                    df = pd.read_html(str(table))[0]
            except Exception as e:
                 print(f"Gagal parse HTML: {e}")

        if not df.empty:
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "putusan_sipp_pn_jakpus.csv")
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"\n[SUKSES] Data berhasi diamankan!")
            print(f"[LOKASI FILE] {output_path}")
            print(df.head(3))
        else:
             print("\n[GAGAL] Tidak ada data yang berhasil diekstrak.")
        
        print("\nMenutup browser dalam 5 detik...")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
