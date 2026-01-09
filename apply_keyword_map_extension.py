# apply_keyword_map_extension.py
import csv
from pathlib import Path

IN = Path("companies_master_final_auto_mapped.csv")
OUT = Path("companies_master_final_auto_mapped_v2.csv")
SUG = Path("keyword_map_suggestions.csv")

# 拡張マップ（頻出トークンを業界にマップ）
EXT_MAP = {
    "介護":"介護・福祉","介護・福祉":"介護・福祉","看護":"介護・福祉","在宅":"介護・福祉",
    "検査":"医療機器メーカー","診断":"医療機器メーカー","画像診断":"医療機器メーカー","医療機器":"医療機器メーカー","装置":"医療機器メーカー",
    "医療データ":"医療IT・医療データ","医療データ・ai":"医療IT・医療データ","医療情報":"医療IT・医療データ","医療saas":"医療IT・医療データ",
    "製薬":"製薬・バイオ","医薬":"製薬・バイオ","バイオ":"製薬・バイオ","薬":"製薬・バイオ",
    "栄養":"ヘルスケア食品・栄養","サプリ":"ヘルスケア食品・栄養","健康食品":"ヘルスケア食品・栄養",
    "流通":"医療卸・流通","卸":"医療卸・流通",
    "物流":"医療物流","配送":"医療物流","倉庫":"医療物流",
    "出版":"医療メディア・出版","メディア":"医療メディア・出版","情報発信":"医療メディア・出版",
    "教育":"教育・研修","研修":"教育・研修","スクール":"教育・研修",
    "フィットネス":"フィットネス・健康サービス","スポーツ":"フィットネス・健康サービス"
}

def find_token_suggestion(text):
    t = (text or "").lower()
    for tok, ind in EXT_MAP.items():
        if tok in t:
            return ind
    return None

# If IN doesn't exist, try fallback to companies_master_final.csv
if not IN.exists():
    IN = Path("companies_master_final.csv")

with IN.open(encoding="utf-8") as f_in, OUT.open("w", encoding="utf-8", newline="") as f_out:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        industry = (row.get("industry") or "").strip()
        if industry == "その他医療関連":
            text = " ".join([row.get("short_description","") or "", row.get("raw_medical_keywords","") or "", row.get("raw_medical_domains","") or ""])
            sug = find_token_suggestion(text)
            if sug:
                row["industry"] = sug
        writer.writerow(row)

print("書き出し完了:", OUT)
