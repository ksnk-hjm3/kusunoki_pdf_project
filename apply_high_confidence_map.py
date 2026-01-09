# apply_high_confidence_map.py
import csv
from pathlib import Path
import subprocess

SUG = Path("manual_industry_map_suggestions.csv")
TEMPLATE = Path("manual_industry_map_template.csv")

if not SUG.exists():
    print("suggestions not found:", SUG); raise SystemExit

# load existing template to preserve manual edits
existing = {}
if TEMPLATE.exists():
    with TEMPLATE.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            existing[r.get("company_id","")] = r.get("force_industry","")

# build map
to_write = []
with SUG.open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cid = r.get("company_id","")
        if not cid: continue
        conf = float(r.get("confidence") or 0)
        suggested = r.get("suggested_industry","").strip()
        if conf >= 0.8 and suggested:
            to_write.append({"company_id":cid,"company_name":r.get("company_name",""),"force_industry":suggested})
        elif cid in existing and existing[cid]:
            to_write.append({"company_id":cid,"company_name":r.get("company_name",""),"force_industry":existing[cid]})

# write template (overwrite)
with TEMPLATE.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_id","company_name","force_industry"])
    w.writeheader()
    for r in to_write:
        w.writerow(r)

print("テンプレート更新:", TEMPLATE)
# call apply_manual_map.py to produce mapped file
subprocess.run(["python","apply_manual_map.py"], check=False)
print("apply_manual_map.py 実行完了")
