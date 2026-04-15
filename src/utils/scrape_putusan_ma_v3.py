"""
Phase 3 v3: Scrape Putusan MA — HTML Page Navigation Strategy
Karena AJAX endpoint diblokir (502/403), kita navigate langsung ke search page
dan scrape DOM result via Playwright.
"""
from __future__ import annotations
import pandas as pd
import time
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://putusan3.mahkamahagung.go.id"

# Simplified queries - fokus yang paling penting
SEARCHES = [
    {"q": "wanprestasi", "label": "wanprestasi"},
    {"q": "investasi", "label": "investasi"},
    {"q": "perizinan", "label": "perizinan"},
    {"q": "pencabutan izin", "label": "pencabutan_izin"},
    {"q": "penipuan", "label": "penipuan"},
    {"q": "penggelapan", "label": "penggelapan"},
    {"q": "tata usaha negara", "label": "tun"},
]

YEARS = ["2020", "2021", "2022", "2023", "2024"]


def scrape_search_page(page, query, tahun, label, page_num=1):
    """Navigate to search result page and scrape the DOM."""
    records = []
    
    # Build URL like the actual search page
    url = f"{BASE}/search/index/?keyword={query}&tahun={tahun}&jenis_doc=Putusan&page={page_num}"
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        
        # Wait for content to render
        page.wait_for_timeout(2000)
        
        content = page.content()
        
        # Check for challenge/captcha
        if "challenge" in content.lower() and "turnstile" in content.lower():
            print("[CF-TURNSTILE]", end=" ")
            page.wait_for_timeout(10000)
            content = page.content()
        
        # Try to find result items via various selectors
        # MA site typically uses table or div-based results
        selectors_to_try = [
            ".result-perkara",
            ".media",
            ".result-item", 
            ".perkara-item",
            "table.table tbody tr",
            "#searchResult .media",
            ".col-md-12 .media",
            ".result h2 a",
            "a[href*='/putusan/']",
            "a[href*='/direktori/putusan/']",
        ]
        
        found_elements = None
        used_selector = None
        
        for selector in selectors_to_try:
            elements = page.query_selector_all(selector)
            if elements and len(elements) > 0:
                found_elements = elements
                used_selector = selector
                break
        
        if found_elements:
            print(f"[{used_selector}: {len(found_elements)} items]", end=" ", flush=True)
            
            for elem in found_elements:
                try:
                    text = elem.inner_text()
                    href = elem.get_attribute("href") or ""
                    
                    # Try to extract structured data
                    record = {
                        "query_label": label,
                        "query": query,
                        "tahun_search": tahun,
                        "source": "html_playwright",
                    }
                    
                    # Extract nomor perkara (pattern: 123/Pdt.G/2024/PN Xxx)
                    nomor_match = re.search(r'(\d+/[A-Za-z\.]+/\d{4}/[A-Z\s\.]+)', text)
                    if nomor_match:
                        record["nomor"] = nomor_match.group(1).strip()
                    
                    # Extract pengadilan
                    pn_match = re.search(r'((?:PN|PT|PA|PTUN|MA)\s+\w+)', text)
                    if pn_match:
                        record["pengadilan"] = pn_match.group(1).strip()
                    
                    # Extract dates (dd-mm-yyyy or dd/mm/yyyy)
                    dates = re.findall(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', text)
                    if dates:
                        record["tanggal_1"] = dates[0]
                        if len(dates) > 1:
                            record["tanggal_2"] = dates[1]
                    
                    # Extract jenis perkara
                    jenis_match = re.search(r'(Pdt\.G|Pdt\.Sus|Pid\.B|Pid\.Sus|TUN|PHI|Pdt)', text)
                    if jenis_match:
                        record["jenis_perkara"] = jenis_match.group(1)
                    
                    # Extract amar/status
                    for keyword in ["Kabul", "Tolak", "Tidak Dapat Diterima", "Gugur", "Damai"]:
                        if keyword.lower() in text.lower():
                            record["amar"] = keyword
                            break
                    
                    # Store full text for later parsing
                    record["raw_text"] = text[:500]
                    
                    if href:
                        record["detail_url"] = href if href.startswith("http") else BASE + href
                    
                    records.append(record)
                    
                except Exception as e:
                    continue
        else:
            # No selectors matched - dump page structure for debugging
            title = page.title()
            body_text = page.inner_text("body")[:300] if page.query_selector("body") else "empty"
            
            # Check if it's a "no results" page
            if "tidak ditemukan" in body_text.lower() or "0 hasil" in body_text.lower():
                print(f"[0 results]", end=" ")
            elif "403" in body_text or "forbidden" in body_text.lower():
                print(f"[403]", end=" ")
            elif "502" in body_text or "bad gateway" in body_text.lower():
                print(f"[502]", end=" ")
            else:
                print(f"[NO_MATCH title='{title[:40]}' body='{body_text[:80]}...']", end=" ")
                
    except Exception as e:
        err_msg = str(e)[:60]
        print(f"[ERR: {err_msg}]", end=" ")
    
    return records


def main():
    print("=" * 70)
    print("PHASE 3 v3: Scraping Putusan MA — HTML Page Navigation")
    print("Target: putusan3.mahkamahagung.go.id")
    print("Strategy: Navigate to search URL, scrape rendered DOM")
    print("=" * 70)
    
    from playwright.sync_api import sync_playwright
    
    all_records = []
    
    with sync_playwright() as p:
        print("\n[LAUNCH] Starting Chromium (stealth mode)...")
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
            extra_http_headers={
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        
        # Anti-detection: remove webdriver flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)
        
        page = context.new_page()
        
        # Step 1: Warm up session on homepage
        print("[STEP 1] Loading homepage...")
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            title = page.title()
            print(f"  Title: '{title}'")
            
            cookies = context.cookies()
            print(f"  Cookies: {len(cookies)}")
            
            if "Direktori" in title or "putusan" in title.lower():
                print("  [OK] Site accessible!")
            else:
                print(f"  [WARN] Unexpected title. Continuing...")
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            print("  Continuing anyway...")
        
        # Step 2: Try a simple test search first
        print("\n[STEP 2] Testing single search page...")
        test_url = f"{BASE}/search/index/?keyword=wanprestasi&tahun=2024&jenis_doc=Putusan"
        try:
            page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            title = page.title()
            print(f"  Test page title: '{title}'")
            
            # Dump full page structure for understanding
            body = page.inner_text("body")[:1000]
            print(f"  Body preview: '{body[:300]}...'")
            
            # Take screenshot for debugging
            debug_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
            os.makedirs(debug_dir, exist_ok=True)
            screenshot_path = os.path.join(debug_dir, "debug_ma_search.png")
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  Screenshot: {screenshot_path}")
            
            # Try to count any links to putusan detail pages
            putusan_links = page.query_selector_all("a[href*='putusan']")
            print(f"  Links containing 'putusan': {len(putusan_links)}")
            
            all_links = page.query_selector_all("a")
            print(f"  Total links on page: {len(all_links)}")
            
            # Print first 10 link hrefs for pattern detection
            for i, link in enumerate(all_links[:15]):
                href = link.get_attribute("href") or ""
                text = link.inner_text()[:50]
                if href and "/putusan" in href.lower() or "/direktori" in href.lower() or "Pdt" in text or "Pid" in text:
                    print(f"    [{i}] href='{href[:80]}' text='{text}'")
                    
        except Exception as e:
            print(f"  [ERROR] Test search failed: {e}")
        
        # Step 3: If test worked, run full scrape
        print(f"\n[STEP 3] Full scrape ({len(SEARCHES)} queries × {len(YEARS)} years)...")
        
        for search in SEARCHES:
            query = search["q"]
            label = search["label"]
            
            for tahun in YEARS:
                print(f"\n  [{label}] {tahun}...", end=" ", flush=True)
                
                results = scrape_search_page(page, query, tahun, label)
                if results:
                    all_records.extend(results)
                    print(f"→ {len(results)} records", end="")
                
                # Rate limit
                time.sleep(3)
        
        # Summary & save
        browser.close()
    
    if all_records:
        df = pd.DataFrame(all_records)
        print(f"\n\n[TOTAL] Raw records: {len(df)}")
        
        if "nomor" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["nomor"])
            print(f"[DEDUP] {before} -> {len(df)} unique")
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "putusan_ma_sample.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[SAVED] {output_path}")
        
        # Stats
        if "query_label" in df.columns:
            print("\n[CATEGORY]:")
            for label, count in df["query_label"].value_counts().items():
                print(f"  {label}: {count}")
        
        if "jenis_perkara" in df.columns:
            print("\n[TYPE]:")
            for j, c in df["jenis_perkara"].value_counts().head(10).items():
                print(f"  {j}: {c}")
        
        print(f"\n[DONE] Phase 3 v3 complete! {len(df)} decisions scraped.")
    else:
        print("\n\n[RESULT] No data collected.")
        print("The search page might be using JS rendering that needs more time,")
        print("or the search endpoint itself is down/blocked.")


if __name__ == "__main__":
    main()
