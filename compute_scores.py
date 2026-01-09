# compute_scores.py
import csv
from pathlib import Path

IN = Path("companies_master_final.csv")
OUT = Path("companies_master_scored.csv")

def side_job_fit(ms):
    if ms >= 90: return 90
    if ms >= 70: return 75
    if ms >= 40: return 60
    if ms >= 10: return 40
    return 20

def career_shift_fit(ms):
    if ms >= 90: return 30
    if ms >= 70: return 40
    if ms >= 40: return 60
    if ms >= 10: return 75
    return 85

def learning_growth(ms):
    if ms >= 80: return 80
    if ms >= 50: return 65
    if ms >= 20: return 50
    return 30

def risk_level(ms, industry):
    # 低い数値 = 低リスク、数値は任意の目安（1-100）
    if industry and "医療機器" in industry:
        base = 40
    elif industry and ("製薬" in industry or "バイオ" in industry):
        base = 50
    elif industry and "医療IT" in industry:
        base = 30
    else:
        base = 45
    # relevance が高いほどリスクはやや低めにする
    if ms >= 80: base -= 10
    if ms <= 10: base += 10
    return max(10, min(90, base))

def target_background_suggestion(industry, ms):
    if industry and "医療IT" in industry:
        return "ITエンジニア;医療現場経験者;データサイエンティスト"
    if industry and "医療機器" in industry:
        return "機械設計;臨床経験者;品質管理"
    if industry and "製薬" in industry or (industry and "バイオ" in industry):
        return "研究職;臨床開発;薬剤師"
    if industry and "介護" in industry:
        return "介護職;看護師;福祉系経験者"
    return "医療関連経験者;業界未経験者歓迎"

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    # ensure fields exist
    for fld in ["side_job_fit_score","career_shift_fit_score","hybrid_fit_score","learning_growth_score","risk_level","target_background"]:
        if fld not in fieldnames:
            fieldnames.append(fld)
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        try:
            ms = int(row.get("medical_relevance_score") or 0)
        except:
            ms = 0
        industry = row.get("industry") or ""
        s = side_job_fit(ms)
        c = career_shift_fit(ms)
        h = int((s + c) / 2)
        lg = learning_growth(ms)
        rl = risk_level(ms, industry)
        tb = target_background_suggestion(industry, ms)
        row["side_job_fit_score"] = s
        row["career_shift_fit_score"] = c
        row["hybrid_fit_score"] = h
        row["learning_growth_score"] = lg
        row["risk_level"] = rl
        row["target_background"] = tb
        writer.writerow(row)

print("書き出し完了:", OUT)
