# generate_manual_map_suggestions.py
import csv
from pathlib import Path

IN_OTHERS = Path("others_companies.csv")
IN_TOP100 = Path("top100_by_score.csv")
OUT = Path("manual_industry_map_suggestions.csv")

# シンプルなキーワード→業界マップ（必要なら私が拡張します）
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

def score_suggestion(text):
    text = (text or "").lower()
    hits = []
    for k,v in KEYWORD_MAP.items():
        if k in text:
            hits.append(v)
    if not hits:
        return None, 0.0
    # 最頻値を候補、confidence = min(0.9, 0.4 + 0.2 * count)
    from collections import Counter
    c = Counter(hits)
    cand, cnt = c.most_common(1)[0]
    confidence = min(0.95, 0.4 + 0.15 * cnt)
    return cand, round(confidence, 2)

def process_file(path, writer):
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            cid = row.get("company_id","").strip()
            name = row.get("company_name","").strip()
            desc = row.get("short_description","")
            raw_k = row.get("raw_medical_keywords","") or ""
            raw_d = row.get("raw_medical_domains","") or ""
            text = " ".join([name, desc, raw_k, raw_d])
            suggested, conf = score_suggestion(text)
            writer.writerow({
                "company_id": cid,
                "company_name": name,
                "suggested_industry": suggested or "",
                "confidence": conf,
                "note": ""
            })

with OUT.open("w", encoding="utf-8", newline="") as f_out:
    fieldnames = ["company_id","company_name","suggested_industry","confidence","note"]
    w = csv.DictWriter(f_out, fieldnames=fieldnames)
    w.writeheader()
    if IN_OTHERS.exists():
        process_file(IN_OTHERS, w)
    if IN_TOP100.exists():
        process_file(IN_TOP100, w)

print("書き出し完了:", OUT)
