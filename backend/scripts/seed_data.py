"""data/usd_krw.csv(실제 USD/KRW 일별 환율)를 API로 업로드한다.

사용: python scripts/seed_data.py [API_BASE_URL]   (기본 http://127.0.0.1:8000)
"""
import csv
import json
import sys
import urllib.request
from pathlib import Path

base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
csv_path = Path(__file__).resolve().parents[2] / "data" / "usd_krw.csv"

with open(csv_path, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for i, r in enumerate(rows, 1):
    body = json.dumps({"date": r["date"], "value": float(r["value"]), "memo": r["memo"]}).encode()
    req = urllib.request.Request(f"{base}/api/data", body, {"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=60).read()
    if i % 20 == 0 or i == len(rows):
        print(f"{i}/{len(rows)} uploaded")
