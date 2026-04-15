"""
Phase 3 v2: Scrape Putusan MA — Advanced Anti-Block Strategy
Strategi:
  1. Playwright (headless browser) — bypass Cloudflare JS challenge
  2. Session cookies dari Playwright → inject ke httpx untuk AJAX calls
  3. Fallback: scrape HTML search results langsung via Playwright
"""
from __future__ import annotations
import json
import pandas as pd
import time
import os
import sys
import asyncio

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://putusan3.mahkamahagung.go.id"

# Search queries relevan LEUI — sama dengan v1
SEARCHES = [
    # H1: Inconsistency risk
    {"q": "wanprestasi kontrak", "label": "wanprestasi_kontrak"},
    {"q": "wanprestasi investasi", "label": "wanprestasi_investasi"},
    # H3: Procedural delay
    {"q": "perizinan usaha", "label": "perizinan_usaha"},
    {"q": "sengketa perizinan", "label": "sengketa_perizinan"},
    # H4: Regulatory reversal
    {"q": "pencabutan izin", "label": "pencabutan_izin"},
    {"q": "tata usaha negara izin", "label": "tun_izin"},
    # H5: Criminal enforcement
    {"q": "penipuan investasi", "label": "penipuan_investasi"},
    {"q": "penggelapan perusahaan", "label": "penggelapan_perusahaan"},
]

YEARS = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]


def extract_decisions_from_page(page, query, tahun, label, max_pages=3):
    """Use Playwright page to do AJAX search and extract decisions."""
    records = []
    
    for pg in range(1, max_pages + 1):
        try:
            # Execute the AJAX POST directly in browser context (bypasses Cloudflare)
            result = page.evaluate("""
                async ([query, tahun, pageNum]) => {
                    try {
                        const resp = await fetch('/search/index/pencarian/ajax/putusan', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest',
                            },
                            body: JSON.stringify({
                                q: query,
                                tahun: tahun,
                                jenis_doc: 'Putusan',
                                page: pageNum,
                            }),
                        });
                        if (!resp.ok) return {error: resp.status, text: await resp.text()};
                        const ct = resp.headers.get('content-type') || '';
                        if (ct.includes('json')) {
                            return await resp.json();
                        } else {
                            return {error: 'not_json', text: (await resp.text()).substring(0, 500)};
                        }
                    } catch(e) {
                        return {error: e.message};
                    }
                }
            """, [query, tahun, pg])
            
            if result is None or "error" in result:
                err = result.get("error", "unknown") if result else "null response"
                if pg == 1:
                    print(f"[ERR:{err}]", end=" ")
                break
            
            decisions = result.get("data", [])
            if not decisions:
                if pg == 1:
                    total = result.get("total", 0)
                    print(f"0/{total}", end=" ")
                break
            
            if pg == 1:
                total = result.get("total", len(decisions))
                print(f"{total} total", end=" ", flush=True)
            
            for d in decisions:
                record = {
                    "nomor": d.get("nomor", ""),
                    "tanggal_musyawarah": d.get("tanggal_musyawarah", ""),
                    "tanggal_registrasi": d.get("tanggal_registrasi", ""),
                    "pengadilan": d.get("pengadilan", ""),
                    "jenis_perkara": d.get("jenis_perkara", d.get("klasifikasi", "")),
                    "tahun_search": tahun,
                    "query_label": label,
                    "query": query,
                }
                for key in ["amar", "status", "klasifikasi", "sub_klasifikasi",
                            "lembaga_peradilan", "provinsi"]:
                    if key in d:
                        record[key] = d[key]
                records.append(record)
            
            time.sleep(1.5)  # Rate limit
            
        except Exception as e:
            print(f"[EXCEPTION: {e}]", end=" ")
            break
    
    return records


def scrape_html_fallback(page, query, tahun, label):
    """Fallback: if AJAX fails, scrape HTML search results directly."""
    records = []
    try:
        url = f"{BASE}/search/index/?keyword={query}&tahun={tahun}&jenis_doc=Putusan"
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
        
        # Check for Cloudflare challenge page
        content = page.content()
        if "cf-browser-verification" in content or "challenge-platform" in content:
            print("[CF-CHALLENGE waiting 10s...]", end=" ", flush=True)
            time.sleep(10)
            content = page.content()
        
        # Try to extract from search results HTML
        rows = page.query_selector_all(".result-item, .search-result-item, table tbody tr, .perkara-item")
        if rows:
            print(f"[HTML:{len(rows)} rows]", end=" ")
            for row in rows:
                text = row.inner_text()
                # Try to parse nomor perkara from text
                record = {
                    "raw_text": text[:300],
                    "tahun_search": tahun,
                    "query_label": label,
                    "query": query,
                    "source": "html_fallback",
                }
                records.append(record)
        else:
            # Check page title / body for clues
            title = page.title()
            body_snippet = content[:500] if len(content) > 0 else "empty"
            print(f"[NO_ROWS title='{title[:30]}']", end=" ")
            
    except Exception as e:
        print(f"[HTML_ERR: {str(e)[:50]}]", end=" ")
    
    return records


def main():
    print("=" * 70)
    print("PHASE 3 v2: Scraping Putusan MA — Playwright Browser Strategy")
    print("Target: putusan3.mahkamahagung.go.id")
    print("=" * 70)
    
    from playwright.sync_api import sync_playwright
    
    all_records = []
    
    with sync_playwright() as p:
        print("\n[LAUNCH] Starting Chromium browser...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        
        page = context.new_page()
        
        # Step 1: Navigate to main page first to get cookies / pass CF
        print("[STEP 1] Navigating to MA homepage to establish session...")
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            title = page.title()
            print(f"  Title: '{title}'")
            
            # Check if Cloudflare challenge
            content = page.content()
            if "challenge" in content.lower() or "cf-browser" in content.lower():
                print("  [!] Cloudflare challenge detected — waiting 15s for resolution...")
                time.sleep(15)
                content = page.content()
                title = page.title()
                print(f"  After wait — Title: '{title}'")
            
            if "Mahkamah" in title or "putusan" in content.lower() or "direktori" in content.lower():
                print("  [OK] Session established!")
            else:
                print(f"  [WARN] Unexpected page. Body prefix: {content[:200]}")
                print("  Continuing anyway...")
            
            # Extract cookies for logging
            cookies = context.cookies()
            cf_cookies = [c for c in cookies if 'cf' in c['name'].lower()]
            print(f"  Cookies: {len(cookies)} total, {len(cf_cookies)} Cloudflare")
            
        except Exception as e:
            print(f"  [ERROR] Could not load homepage: {e}")
            print("  Attempting to continue anyway...")
        
        # Step 2: Try AJAX search via browser context
        print(f"\n[STEP 2] Starting AJAX search ({len(SEARCHES)} queries × {len(YEARS)} years)...")
        
        ajax_success = False
        
        for search in SEARCHES:
            query = search["q"]
            label = search["label"]
            
            for tahun in YEARS:
                print(f"\n  [{label}] {tahun}...", end=" ", flush=True)
                
                results = extract_decisions_from_page(page, query, tahun, label, max_pages=3)
                
                if results:
                    all_records.extend(results)
                    ajax_success = True
                    print(f"→ {len(results)} records", end="")
                
                time.sleep(1)
        
        # Step 3: If AJAX failed for everything, try HTML scraping as fallback
        if not ajax_success:
            print("\n\n[STEP 3] AJAX failed — trying HTML scraper fallback...")
            
            # Only try a subset to test
            test_queries = SEARCHES[:3]
            test_years = ["2023", "2024"]
            
            for search in test_queries:
                for tahun in test_years:
                    print(f"\n  [HTML] '{search['q']}' {tahun}...", end=" ", flush=True)
                    results = scrape_html_fallback(page, search["q"], tahun, search["label"])
                    if results:
                        all_records.extend(results)
                    time.sleep(2)
        
        # Step 4: Screenshot for debugging if no data
        if not all_records:
            print("\n\n[DEBUG] No data collected. Taking screenshot...")
            screenshot_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "debug_ma_screenshot.png")
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  Screenshot saved: {screenshot_path}")
            
            # Dump page info
            print(f"  Current URL: {page.url}")
            print(f"  Title: {page.title()}")
            cookies = context.cookies()
            print(f"  Cookies ({len(cookies)}):")
            for c in cookies:
                print(f"    {c['name']}: {c['value'][:30]}...")
        
        browser.close()
    
    # Save results
    if all_records:
        df = pd.DataFrame(all_records)
        before = len(df)
        if "nomor" in df.columns:
            df = df.drop_duplicates(subset=["nomor"])
        print(f"\n\n[DEDUP] {before} -> {len(df)} unique decisions")
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "putusan_ma_sample.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[SAVED] {output_path}")
        
        # Summary
        if "query_label" in df.columns:
            print("\n[CATEGORY]:")
            for label, count in df["query_label"].value_counts().items():
                print(f"  {label}: {count}")
        
        if "tahun_search" in df.columns:
            print("\n[YEAR]:")
            for y, c in df["tahun_search"].value_counts().sort_index().items():
                print(f"  {y}: {c}")
        
        if "jenis_perkara" in df.columns:
            print("\n[TYPE]:")
            for j, c in df["jenis_perkara"].value_counts().head(10).items():
                print(f"  {j}: {c}")
        
        # Durasi perkara
        if "tanggal_registrasi" in df.columns and "tanggal_musyawarah" in df.columns:
            try:
                df["tgl_reg"] = pd.to_datetime(df["tanggal_registrasi"], errors="coerce")
                df["tgl_mus"] = pd.to_datetime(df["tanggal_musyawarah"], errors="coerce")
                df["durasi_hari"] = (df["tgl_mus"] - df["tgl_reg"]).dt.days
                valid_dur = df[df["durasi_hari"] > 0]["durasi_hari"]
                if not valid_dur.empty:
                    print(f"\n[DURASI] Mean: {valid_dur.mean():.0f} hari | Median: {valid_dur.median():.0f} | Max: {valid_dur.max()}")
            except Exception:
                pass
        
        print("\n[DONE] Phase 3 v2 complete!")
    else:
        print("\n\n[FAILED] No data collected from any method.")
        print("Possible causes:")
        print("  1. putusan3.mahkamahagung.go.id is down")
        print("  2. Your IP is permanently blocked by Cloudflare")
        print("  3. The site requires Indonesian IP (geo-blocking)")
        print("Recommendation: Try from Indonesian VPN or residential IP")


if __name__ == "__main__":
    main()
