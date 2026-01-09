# refine_templates_v2.py
import csv
from pathlib import Path

IN = Path("companies_master_reclassified_v3.csv")
OUT = Path("companies_master_refined_v2.csv")

templates = {
    "医療機器メーカー": "医療機器の開発・製造を行い、医療現場で使われる製品を提供しています。",
    "製薬・バイオ": "医薬品やバイオ製品の研究開発・製造を行い、治療に用いられる薬を提供しています。",
    "医療IT・医療データ": "医療×ITでシステムやデータサービスを提供し、現場の業務効率化を支援します。",
    "介護・福祉": "介護・福祉サービスを提供し、高齢者支援や在宅ケアを行っています。",
    "医療卸・流通": "医薬品や医療機器の流通を担い、医療機関への安定供給を支えます。",
    "医療物流": "医薬品や医療機器の輸送・保管を行い、物流インフラを提供します。",
    "ヘルスケア食品・栄養": "健康食品や栄養製品を展開し、日常の健康づくりを支援します。",
    "医療メディア・出版": "医療分野の情報発信や出版を行い、学びの基盤を提供します。",
    "教育・研修": "医療・看護分野の教育や研修サービスを提供しています。",
}

def jlen(s):
    return len(s or "")

def fit_text(text, industry):
    text = (text or "").strip()
    if jlen(text) < 30:
        tpl = templates.get(industry)
        if tpl:
            text = tpl
    if jlen(text) > 45:
        text = text[:44] + "…"
    return text

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        row["short_description"] = fit_text(row.get("short_description"), row.get("industry"))
        writer.writerow(row)

print("書き出し完了:", OUT)
