# summary_report.py
import csv
from collections import Counter
from pathlib import Path

IN = Path("companies_master_refined_v2.csv")
OUT_STATS = Path("companies_master_stats.txt")
OUT_TOP = Path("companies_top100_by_score.csv")

rows = []
with IN.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            row["medical_relevance_score"] = int(row.get("medical_relevance_score") or 0)
        except:
            row["medical_relevance_score"] = 0
        rows.append(row)

# industry counts
cnt = Counter([r.get("industry") or "その他" for r in rows])
# score distribution buckets
buckets = Counter()
for r in rows:
    s = r["medical_relevance_score"]
    if s >= 80: buckets["80+"] += 1
    elif s >= 50: buckets["50-79"] += 1
    elif s >= 20: buckets["20-49"] += 1
    else: buckets["0-19"] += 1

with OUT_STATS.open("w", encoding="utf-8") as f:
    f.write("業界別件数\n")
    for k, v in cnt.most_common():
        f.write(f"{k}: {v}\n")
    f.write("\nスコア分布\n")
    for k, v in buckets.items():
        f.write(f"{k}: {v}\n")

# top 100 by medical_relevance_score
rows_sorted = sorted(rows, key=lambda x: x["medical_relevance_score"], reverse=True)
fieldnames = reader.fieldnames
with OUT_TOP.open("w", encoding="utf-8", newline="") as f:
    import csv as _csv
    w = _csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows_sorted[:100]:
        w.writerow(r)

print("統計出力:", OUT_STATS)
print("上位100社出力:", OUT_TOP)
