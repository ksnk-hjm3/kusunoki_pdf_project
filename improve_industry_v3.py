# improve_industry_v3.py
import csv
from pathlib import Path

IN = Path("companies_master_with_meta.csv")
OUT = Path("companies_master_reclassified_v4.csv")

KEYWORD_MAP = {
    "医療it":"医療IT・医療データ","システム":"医療IT・医療データ","データ":"医療IT・医療データ","dx":"医療IT・医療データ","オンライン":"医療IT・医療データ",
    "機器":"医療機器メーカー","検査":"医療機器メーカー","装置":"医療機器メーカー","画像":"医療機器メーカー",
    "製薬":"製薬・バイオ","医薬":"製薬・バイオ","バイオ":"製薬・バイオ","薬":"製薬・バイオ",
    "介護":"介護・福祉","在宅":"介護・福祉","福祉":"介護・福祉","看護":"介護・福祉",
    "流通":"医療卸・流通","卸":"医療卸・流通",
    "物流":"医療物流","配送":"医療物流","倉庫":"医療物流",
    "栄養":"ヘルスケア食品・栄養","サプリ":"ヘルスケア食品・栄養","健康食品":"ヘルスケア食品・栄養",
    "出版":"医療メディア・出版","メディア":"医療メディア・出版","情報発信":"医療メディア・出版",
    "教育":"教育・研修","研修":"教育・研修","スクール":"教育・研修",
    "フィットネス":"フィットネス・健康サービス","スポーツ":"フィットネス・健康サービス",
}

def classify_row(row):
    text = " ".join([
        (row.get("company_name") or ""),
        (row.get("short_description") or ""),
        (row.get("raw_medical_keywords") or ""),
        (row.get("raw_medical_domains") or "")
    ]).lower()
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
        row["industry"] = classify_row(row)
        writer.writerow(row)

print("書き出し完了:", OUT)
