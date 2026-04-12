from __future__ import annotations
import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def search_ddg(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    
    print(f"[SEARCHING] {query}")
    try:
        resp = requests.post(url, headers=headers, data={'q': query}, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = soup.find_all('div', class_='result__body')
        print(f"Found {len(results)} results from DDG.")
        
        extracted_cases = []
        for r in results:
            title_node = r.find('a', class_='result__url')
            snippet_node = r.find('a', class_='result__snippet')
            
            if not title_node or not snippet_node:
                continue
                
            link = title_node.get('href')
            snippet = snippet_node.text.strip()
            
            case_match = re.search(r'\b\d+/[A-Za-z\.]+(?:-[A-Za-z]+)?/\d{4}/?[A-Za-z\. ]*\b', snippet)
            case_no = case_match.group(0) if case_match else "Gagal ekstrak nomor"
            
            extracted_cases.append({
                "link": link,
                "snippet": snippet,
                "nomor_putusan": case_no
            })
            
            print(f"  -> Nomor: {case_no}")
            print(f"     Snip: {snippet[:100]}...")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    search_ddg('site:putusan3.mahkamahagung.go.id "wanprestasi" "investasi"')
    print("-" * 40)
    search_ddg('site:putusan3.mahkamahagung.go.id "pencabutan izin" "tata usaha negara"')
