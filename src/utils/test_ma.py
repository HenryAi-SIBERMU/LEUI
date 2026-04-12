"""Quick test: single query to Putusan MA with 90s timeout"""
import requests, json, urllib3, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://putusan3.mahkamahagung.go.id"
print("[TEST] Single query with 90s timeout...")

try:
    resp = requests.post(
        f"{BASE}/search/index/pencarian/ajax/putusan",
        json={"q": "wanprestasi", "tahun": "2024", "jenis_doc": "Putusan", "page": 1},
        headers={"X-Requested-With": "XMLHttpRequest"},
        timeout=90,
        verify=False,
    )
    print(f"Status: {resp.status_code}")
    ct = resp.headers.get("content-type", "unknown")
    print(f"Content-Type: {ct}")
    print(f"Body size: {len(resp.text)} bytes")
    print(f"Body preview: {resp.text[:1500]}")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
