# extract_others.py
import csv
from pathlib import Path

IN = Path("companies_master_final.csv")
OUT = Path("others_companies.csv")

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = ["company_id","company_name","medical_relevance_score","short_description","raw_medical_keywords","raw_medical_domains"]
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        if (row.get("industry") or "").strip() == "その他医療関連":
            writer.writerow({
                "company_id": row.get("company_id",""),
                "company_name": row.get("company_name",""),
                "medical_relevance_score": row.get("medical_relevance_score",""),
                "short_description": row.get("short_description",""),
                "raw_medical_keywords": row.get("raw_medical_keywords",""),
                "raw_medical_domains": row.get("raw_medical_domains",""),
            })

print("書き出し完了:", OUT)
