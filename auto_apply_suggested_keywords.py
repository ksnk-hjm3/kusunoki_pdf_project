# auto_apply_suggested_keywords.py
import csv
from pathlib import Path

IN = Path("companies_master_final_mapped.csv")
SUG = Path("keyword_map_suggestions.csv")
OUT = Path("companies_master_final_auto_mapped.csv")

# load suggestions token->industry
smap = {}
if SUG.exists():
    with SUG.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            tok = (row.get("token") or "").strip().lower()
            ind = (row.get("suggested_industry") or "").strip()
            if tok and ind:
                smap[tok] = ind

def find_suggestion(row):
    text = " ".join([row.get("raw_medical_keywords","") or "", row.get("raw_medical_domains","") or "", row.get("short_description","") or ""]).lower()
    for tok, ind in smap.items():
        if tok in text:
            return ind
    return None

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        if (row.get("industry") or "").strip() == "その他医療関連":
            sug = find_suggestion(row)
            if sug:
                row["industry"] = sug
        writer.writerow(row)

print("書き出し完了:", OUT)
