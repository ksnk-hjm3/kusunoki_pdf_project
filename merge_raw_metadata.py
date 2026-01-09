# merge_raw_metadata.py
import csv
from pathlib import Path

RAW = Path("raw_companies.csv")
IN = Path("companies_master_final.csv")
OUT = Path("companies_master_with_meta.csv")

# load raw metadata by company_name (lowercased)
meta = {}
with RAW.open(encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        key = (row.get("company_name") or "").strip().lower()
        if not key:
            continue
        meta[key] = {
            "raw_medical_keywords": row.get("medical_keywords") or "",
            "raw_medical_domains": row.get("medical_domains") or "",
            "raw_total_medical_score": row.get("total_medical_score") or row.get("medical_keyword_count") or ""
        }

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames + ["raw_medical_keywords", "raw_medical_domains", "raw_total_medical_score"]
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        key = (row.get("company_name") or "").strip().lower()
        m = meta.get(key, {})
        row["raw_medical_keywords"] = m.get("raw_medical_keywords", "")
        row["raw_medical_domains"] = m.get("raw_medical_domains", "")
        row["raw_total_medical_score"] = m.get("raw_total_medical_score", "")
        writer.writerow(row)

print("書き出し完了:", OUT)
