# stats.py
import csv
from collections import Counter
from pathlib import Path

P = Path("companies_master_final.csv")
if not P.exists():
    P = Path("companies_master_final_auto_mapped_v2.csv")

with P.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

cnt = Counter([r.get("industry") or "その他" for r in rows])
print("業界上位10:")
for k, v in cnt.most_common(10):
    print(k, v)
scores = [int(r.get("medical_relevance_score") or 0) for r in rows]
print("件数", len(rows), "平均", (sum(scores)/len(scores)) if scores else 0)
