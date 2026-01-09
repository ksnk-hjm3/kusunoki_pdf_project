# rescale_scores.py
import csv
from pathlib import Path
import numpy as np

IN = Path("companies_master_reclassified_v4.csv")
OUT = Path("companies_master_scored_v2.csv")

rows = []
with IN.open(encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        try:
            row["medical_relevance_score"] = int(row.get("medical_relevance_score") or 0)
        except:
            row["medical_relevance_score"] = 0
        rows.append(row)

scores = np.array([r["medical_relevance_score"] for r in rows])
if len(scores) == 0:
    raise SystemExit("データがありません")

# パーセンタイル正規化（0-100）
pcts = np.percentile(scores, np.linspace(0,100,101))
def percentile_scale(x):
    # x を 0-100 にマップ（0-100 のままだが分布を滑らかに）
    return int(np.interp(x, pcts, np.linspace(0,100,101)))

for r in rows:
    ms = r["medical_relevance_score"]
    ms_scaled = percentile_scale(ms)
    r["medical_relevance_score"] = ms_scaled
    # 再計算ルール（例）
    if ms_scaled >= 85:
        s = 90; c = 30
    elif ms_scaled >= 65:
        s = 75; c = 40
    elif ms_scaled >= 40:
        s = 60; c = 60
    elif ms_scaled >= 15:
        s = 45; c = 75
    else:
        s = 25; c = 85
    r["side_job_fit_score"] = s
    r["career_shift_fit_score"] = c
    r["hybrid_fit_score"] = int((s + c) / 2)
    # learning_growth: ms_scaled に応じて
    if ms_scaled >= 80: lg = 80
    elif ms_scaled >= 50: lg = 65
    elif ms_scaled >= 20: lg = 45
    else: lg = 30
    r["learning_growth_score"] = lg
    # risk_level: 業界ベース微調整
    ind = (r.get("industry") or "")
    base = 45
    if "医療機器" in ind: base = 40
    if "製薬" in ind or "バイオ" in ind: base = 50
    if "医療it" in ind or "医療IT" in ind: base = 30
    if ms_scaled >= 80: base -= 10
    if ms_scaled <= 10: base += 10
    r["risk_level"] = max(10, min(90, base))

# write out
with OUT.open("w", encoding="utf-8", newline="") as f_out:
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print("書き出し完了:", OUT)
