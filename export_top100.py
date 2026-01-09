# export_top100.py
import csv
from pathlib import Path

IN = Path("companies_master_final.csv")
OUT = Path("top100_by_score.csv")

rows = []
with IN.open(encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        try:
            row["medical_relevance_score"] = int(row.get("medical_relevance_score") or 0)
        except:
            row["medical_relevance_score"] = 0
        rows.append(row)

rows_sorted = sorted(rows, key=lambda x: x["medical_relevance_score"], reverse=True)
fieldnames = ["company_id","company_name","medical_relevance_score","industry","short_description","raw_medical_keywords","raw_medical_domains"]
with OUT.open("w", encoding="utf-8", newline="") as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows_sorted[:100]:
        writer.writerow({k: r.get(k,"") for k in fieldnames})

print("書き出し完了:", OUT)
