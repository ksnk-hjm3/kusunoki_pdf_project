# gen_manual_map_template.py
from pathlib import Path
import csv

OUT = Path("manual_industry_map_template.csv")
fieldnames = ["company_id","company_name","force_industry"]

with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

print("テンプレート作成:", OUT)
