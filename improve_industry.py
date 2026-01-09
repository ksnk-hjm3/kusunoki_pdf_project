# improve_industry.py
import csv
from pathlib import Path

IN = Path("companies_master_scored.csv")
OUT = Path("companies_master_reclassified_v2.csv")

def classify(row):
    name = (row.get("company_name") or "").lower()
    desc = (row.get("short_description") or "").lower()
    text = name + " " + desc
    if "it" in text or "システム" in text or "データ" in text or "dx" in text or "オンライン" in text:
        return "医療IT・医療データ"
    if "機器" in text or "検査" in text or "画像" in text or "装置" in text:
        return "医療機器メーカー"
    if "製薬" in text or "医薬" in text or "バイオ" in text or "薬" in text:
        return "製薬・バイオ"
    if "介護" in text or "在宅" in text or "福祉" in text:
        return "介護・福祉"
    if "物流" in text or "配送" in text or "倉庫" in text:
        return "医療物流"
    if "流通" in text or "卸" in text or "供給" in text:
        return "医療卸・流通"
    if "栄養" in text or "サプリ" in text or "健康食品" in text:
        return "ヘルスケア食品・栄養"
    if "出版" in text or "メディア" in text or "情報発信" in text:
        return "医療メディア・出版"
    if "教育" in text or "研修" in text or "スクール" in text:
        return "教育・研修"
    return row.get("industry") or "その他医療関連"

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        row["industry"] = classify(row)
        writer.writerow(row)

print("書き出し完了:", OUT)
