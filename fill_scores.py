# fill_scores.py
import csv
from pathlib import Path

IN = Path("companies_master.csv")
OUT = Path("companies_master_scored.csv")

def compute_side_job_fit(med_score):
    if med_score >= 80:
        return 80
    if med_score >= 40:
        return 60
    if med_score >= 10:
        return 40
    return 20

def compute_career_shift_fit(med_score):
    if med_score >= 80:
        return 30
    if med_score >= 40:
        return 50
    if med_score >= 10:
        return 70
    return 80

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        try:
            ms = int(row.get("medical_relevance_score") or 0)
        except:
            ms = 0
        row["side_job_fit_score"] = compute_side_job_fit(ms)
        row["career_shift_fit_score"] = compute_career_shift_fit(ms)
        # hybrid は平均（例）
        row["hybrid_fit_score"] = int((int(row["side_job_fit_score"]) + int(row["career_shift_fit_score"])) / 2)
        writer.writerow(row)

print("書き出し完了:", OUT)
