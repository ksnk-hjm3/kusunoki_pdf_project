# reclassify_industry.py
import csv
from pathlib import Path

IN = Path("companies_master.csv")
OUT = Path("companies_master_reclassified.csv")

def classify_by_keywords(row):
    kw = (row.get("short_description") or "") + "," + (row.get("company_name") or "") + "," + (row.get("industry") or "")
    kw = kw.lower()
    if "医療機器" in kw or "検査" in kw or "画像" in kw:
        return "医療機器メーカー"
    if "製薬" in kw or "医薬" in kw or "バイオ" in kw:
        return "製薬・バイオ"
    if "オンライン" in kw or "it" in kw or "データ" in kw or "dx" in kw or "システム" in kw:
        return "医療IT・医療データ"
    if "介護" in kw or "在宅" in kw or "福祉" in kw:
        return "介護・福祉"
    if "流通" in kw or "卸" in kw or "供給" in kw:
        return "医療卸・流通"
    if "物流" in kw or "配送" in kw:
        return "医療物流"
    if "衛生" in kw or "感染" in kw or "マスク" in kw:
        return "衛生・感染対策"
    if "栄養" in kw or "サプリ" in kw or "健康食品" in kw:
        return "ヘルスケア食品・栄養"
    if "フィットネス" in kw or "運動" in kw:
        return "フィットネス・健康サービス"
    if "出版" in kw or "メディア" in kw or "情報発信" in kw:
        return "医療メディア・出版"
    if "教育" in kw or "研修" in kw or "スクール" in kw:
        return "教育・研修"
    return row.get("industry") or "その他医療関連"

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        row["industry"] = classify_by_keywords(row)
        writer.writerow(row)

print("書き出し完了:", OUT)
