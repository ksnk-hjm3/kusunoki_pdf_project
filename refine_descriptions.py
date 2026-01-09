# refine_descriptions.py
import csv
from pathlib import Path

IN = Path("companies_master_scored.csv")
OUT = Path("companies_master_refined.csv")

def shorten(text, max_len=45):
    if len(text) <= max_len:
        return text
    return text[:max_len-1] + "…"

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        desc = row.get("short_description") or ""
        row["short_description"] = shorten(desc, max_len=45)
        writer.writerow(row)

print("書き出し完了:", OUT)
