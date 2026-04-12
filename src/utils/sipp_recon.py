"""
SIPP RECON - Scan puluhan server SIPP Pengadilan Negeri
untuk menemukan yang TIDAK dilindungi Cloudflare/reCAPTCHA.

Ada 350+ PN di Indonesia. Tidak mungkin semua sudah upgrade WAF.
"""
from __future__ import annotations
import sys
import requests
import urllib3
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Daftar subdomain SIPP dari berbagai PN di Indonesia
# Format: sipp.pn-{nama}.go.id
SIPP_COURTS = [
    # Jawa
    "pn-jakartapusat", "pn-jakartaselatan", "pn-jakartabarat",
    "pn-jakartatimur", "pn-jakartautara",
    "pn-bandung", "pn-surabaya", "pn-semarang", "pn-yogyakarta",
    "pn-bekasi", "pn-tangerang", "pn-depok", "pn-bogor",
    "pn-cirebon", "pn-tasikmalaya", "pn-purwokerto", "pn-solo",
    "pn-malang", "pn-kediri", "pn-sidoarjo", "pn-gresik",
    # Sumatera
    "pn-medan", "pn-palembang", "pn-padang", "pn-pekanbaru",
    "pn-lampung", "pn-jambi", "pn-bengkulu", "pn-batam",
    "pn-bandaaceh", "pn-binjai", "pn-lubukpakam",
    # Kalimantan
    "pn-balikpapan", "pn-samarinda", "pn-pontianak", "pn-banjarmasin",
    "pn-palangkaraya",
    # Sulawesi
    "pn-makassar", "pn-manado", "pn-palu", "pn-kendari", "pn-gorontalo",
    # NTT/NTB/Bali
    "pn-denpasar", "pn-mataram", "pn-kupang", "pn-negara",
    "pn-singaraja", "pn-gianyar", "pn-tabanan",
    # Papua & Maluku
    "pn-jayapura", "pn-ambon", "pn-sorong", "pn-ternate",
    # Lain-lain (kota kecil yang mungkin belum upgrade)
    "pn-bale-bandung", "pn-cianjur", "pn-garut", "pn-sukabumi",
    "pn-karawang", "pn-subang", "pn-indramayu", "pn-majalengka",
    "pn-kuningan", "pn-sumedang",
    "pn-klaten", "pn-wonogiri", "pn-boyolali", "pn-sragen",
    "pn-blitar", "pn-tulungagung", "pn-jombang", "pn-mojokerto",
    "pn-lamongan", "pn-tuban", "pn-bangkalan", "pn-sampang",
    "pn-pamekasan", "pn-sumenep",
    "pn-tanjungkarang", "pn-kotabumi", "pn-metro",
    "pn-bukittinggi", "pn-payakumbuh", "pn-solok",
    "pn-kisaran", "pn-rantauprapat", "pn-pematangsiantar",
    "pn-tebingtinggi", "pn-stabat",
]

def test_sipp(court_name):
    """Test apakah SIPP court ini terbuka tanpa Captcha."""
    url = f"https://sipp.{court_name}.go.id/list_perkara"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        resp = requests.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)
        body = resp.text[:2000].lower()
        
        has_captcha = "recaptcha" in body or "captcha" in body
        has_cloudflare = "cf-browser-verification" in body or "cf_clearance" in body or "turnstile" in body or "challenges.cloudflare" in body
        has_table = "<table" in body
        has_perkara = "perkara" in body
        
        status = "UNKNOWN"
        if has_captcha or has_cloudflare:
            status = "BLOCKED (Captcha/CF)"
        elif resp.status_code == 403:
            status = "BLOCKED (403)"
        elif has_table and has_perkara:
            status = "*** OPEN (Table Found!) ***"
        elif has_perkara:
            status = "** PARTIAL (Perkara keyword, no table) **"
        elif resp.status_code == 200:
            status = "OK but unknown content"
        else:
            status = f"HTTP {resp.status_code}"
            
        return (court_name, status, resp.status_code, has_table, has_captcha)
    except requests.exceptions.Timeout:
        return (court_name, "TIMEOUT", 0, False, False)
    except requests.exceptions.ConnectionError:
        return (court_name, "CONNECTION ERROR", 0, False, False)
    except Exception as e:
        return (court_name, f"ERROR: {str(e)[:50]}", 0, False, False)


def main():
    print("=" * 70)
    print("SIPP RECON - Scanning 80+ Pengadilan Negeri di Indonesia")
    print("Mencari server yang TIDAK dilindungi Cloudflare/reCAPTCHA...")
    print("=" * 70)
    
    open_courts = []
    partial_courts = []
    blocked_courts = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(test_sipp, court): court for court in SIPP_COURTS}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            court_name, status, code, has_table, has_captcha = future.result()
            icon = ""
            if "OPEN" in status:
                icon = "[TERBUKA]"
                open_courts.append(court_name)
            elif "PARTIAL" in status:
                icon = "[POTENSIAL]"
                partial_courts.append(court_name)
            elif "BLOCKED" in status:
                icon = "[DIBLOKIR]"
                blocked_courts.append(court_name)
            else:
                icon = "[?]"
                
            print(f"  {icon} sipp.{court_name}.go.id -> {status}")
    
    print("\n" + "=" * 70)
    print("HASIL RECON:")
    print("=" * 70)
    print(f"\n  SERVER TERBUKA (bisa di-scrape langsung): {len(open_courts)}")
    for c in open_courts:
        print(f"    -> https://sipp.{c}.go.id/list_perkara")
    print(f"\n  SERVER POTENSIAL (perlu investigasi lanjut): {len(partial_courts)}")
    for c in partial_courts:
        print(f"    -> https://sipp.{c}.go.id/list_perkara")
    print(f"\n  SERVER DIBLOKIR (Captcha/CF): {len(blocked_courts)}")
    print(f"\n  TOTAL SCANNED: {len(SIPP_COURTS)}")


if __name__ == "__main__":
    main()
