import csv
from pathlib import Path

IN = Path("companies_master_final.csv")
MAP = Path("manual_industry_map_template.csv")
OUT = Path("companies_master_final_mapped.csv")

mapping = {}
if MAP.exists():
    with MAP.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            cid = (row.get("company_id") or "").strip()
            if cid:
                mapping[cid] = row.get("force_industry","").strip()

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        cid = (row.get("company_id","") or "").strip()
        if cid in mapping and mapping[cid]:
            row["industry"] = mapping[cid]
        writer.writerow(row)

print("書き出し完了:", OUT)
