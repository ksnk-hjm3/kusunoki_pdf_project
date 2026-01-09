# improve_industry_v2.py
import csv
from pathlib import Path

IN = Path("companies_master_final.csv")
OUT = Path("companies_master_reclassified_v3.csv")

# 追加キーワードマップ（必要ならこちらで拡張します）
KEYWORD_MAP = {
    "医療it": "医療IT・医療データ",
    "システム": "医療IT・医療データ",
    "データ": "医療IT・医療データ",
    "dx": "医療IT・医療データ",
    "オンライン": "医療IT・医療データ",
    "機器": "医療機器メーカー",
    "検査": "医療機器メーカー",
    "装置": "医療機器メーカー",
    "製薬": "製薬・バイオ",
    "医薬": "製薬・バイオ",
    "バイオ": "製薬・バイオ",
    "介護": "介護・福祉",
    "在宅": "介護・福祉",
    "福祉": "介護・福祉",
    "流通": "医療卸・流通",
    "卸": "医療卸・流通",
    "物流": "医療物流",
    "配送": "医療物流",
    "栄養": "ヘルスケア食品・栄養",
    "サプリ": "ヘルスケア食品・栄養",
    "出版": "医療メディア・出版",
    "メディア": "医療メディア・出版",
    "教育": "教育・研修",
    "研修": "教育・研修",
}

def classify(row):
    name = (row.get("company_name") or "").lower()
    desc = (row.get("short_description") or "").lower()
    text = name + " " + desc
    # 優先度の高いキーワードから判定
    for k, v in KEYWORD_MAP.items():
        if k in text:
            return v
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
