# finalize_templates_and_scores.py
import csv
from pathlib import Path

IN = Path("companies_master_final_auto_mapped_v2.csv")
OUT = Path("companies_master_final.csv")

# 業界ごとの最終テンプレ（短め・自然な文）
TEMPLATES = {
    "医療機器メーカー":"医療機器の開発・製造を行い、医療現場で使われる製品を提供しています。",
    "製薬・バイオ":"医薬品やバイオ製品の研究開発・製造を行い、治療に用いられる薬を提供しています。",
    "医療IT・医療データ":"医療×ITでシステムやデータサービスを提供し、現場の効率化を支援します。",
    "介護・福祉":"介護・福祉サービスを提供し、高齢者支援や在宅ケアを行っています。",
    "医療卸・流通":"医薬品や医療機器の流通を担い、医療機関への安定供給を支えます。",
    "医療物流":"医薬品や医療機器の輸送・保管を行い、物流インフラを提供します。",
    "ヘルスケア食品・栄養":"健康食品や栄養製品を展開し、日常の健康づくりを支援します。",
    "医療メディア・出版":"医療分野の情報発信や出版を行い、学びの基盤を提供します。",
    "教育・研修":"医療・看護分野の教育や研修サービスを提供しています。",
    "フィットネス・健康サービス":"運動や健康サービスを提供し、生活習慣改善を支援します。"
}

# スコア微調整ルール（最終）
def recompute_scores(ms, industry):
    # ms は 0-100 想定
    if ms >= 85:
        s, c, lg = 90, 30, 80
    elif ms >= 65:
        s, c, lg = 75, 40, 65
    elif ms >= 40:
        s, c, lg = 60, 60, 50
    elif ms >= 15:
        s, c, lg = 45, 75, 40
    else:
        s, c, lg = 25, 85, 30
    h = int((s + c) / 2)
    base = 45
    if "医療機器" in (industry or ""): base = 40
    if "製薬" in (industry or "") or "バイオ" in (industry or ""): base = 50
    if "医療IT" in (industry or ""): base = 30
    if ms >= 80: base -= 10
    if ms <= 10: base += 10
    rl = max(10, min(90, base))
    return s, c, h, lg, rl

# If IN missing, fallback
if not IN.exists():
    IN = Path("companies_master_final_auto_mapped.csv")

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    # ensure fields exist
    for fld in ["side_job_fit_score","career_shift_fit_score","hybrid_fit_score","learning_growth_score","risk_level","target_background","short_description"]:
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
        s, c, h, lg, rl = recompute_scores(ms, industry)
        row["side_job_fit_score"] = s
        row["career_shift_fit_score"] = c
        row["hybrid_fit_score"] = h
        row["learning_growth_score"] = lg
        row["risk_level"] = rl
        # target_background は業界ベースで簡易設定
        if "医療IT" in industry:
            row["target_background"] = "ITエンジニア;医療現場経験者;データサイエンティスト"
        elif "医療機器" in industry:
            row["target_background"] = "機械設計;臨床経験者;品質管理"
        elif "製薬" in industry or "バイオ" in industry:
            row["target_background"] = "研究職;臨床開発;薬剤師"
        elif "介護" in industry:
            row["target_background"] = "介護職;看護師;福祉系経験者"
        else:
            row["target_background"] = "医療関連経験者;業界未経験者歓迎"
        # short_description をテンプレで補填または切り詰め
        sd = (row.get("short_description") or "").strip()
        if len(sd) < 30:
            tpl = TEMPLATES.get(industry)
            if tpl:
                sd = tpl
        if len(sd) > 45:
            sd = sd[:44] + "…"
        row["short_description"] = sd
        writer.writerow(row)

print("書き出し完了:", OUT)
