# analyze_keywords_and_suggest_map.py
import csv
from collections import Counter, defaultdict
from pathlib import Path
IN = Path("companies_master_final_mapped.csv")
OUT_FREQ = Path("keyword_frequency.csv")
OUT_SUG = Path("keyword_map_suggestions.csv")

counter = Counter()
domain_counter = Counter()
rows = []
with IN.open(encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(row)
        kws = (row.get("raw_medical_keywords") or "")
        doms = (row.get("raw_medical_domains") or "")
        for part in [kws, doms]:
            for token in [t.strip().lower() for t in part.replace(';',',').split(',') if t.strip()]:
                counter[token] += 1

# write frequency
with OUT_FREQ.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["token","count"])
    for tok, cnt in counter.most_common():
        w.writerow([tok, cnt])

# simple heuristic suggestions: map tokens containing keywords to industries
INDUSTRY_HINTS = {
    "it":"医療IT・医療データ","システム":"医療IT・医療データ","データ":"医療IT・医療データ",
    "機器":"医療機器メーカー","検査":"医療機器メーカー","画像":"医療機器メーカー",
    "製薬":"製薬・バイオ","バイオ":"製薬・バイオ","薬":"製薬・バイオ",
    "介護":"介護・福祉","在宅":"介護・福祉","福祉":"介護・福祉",
    "栄養":"ヘルスケア食品・栄養","サプリ":"ヘルスケア食品・栄養",
    "出版":"医療メディア・出版","教育":"教育・研修","物流":"医療物流","流通":"医療卸・流通",
    "フィットネス":"フィットネス・健康サービス"
}

suggests = []
for tok, cnt in counter.most_common():
    for k, ind in INDUSTRY_HINTS.items():
        if k in tok:
            suggests.append((tok, cnt, ind))
            break

with OUT_SUG.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["token","count","suggested_industry"])
    for tok, cnt, ind in suggests:
        w.writerow([tok, cnt, ind])

print("頻度出力:", OUT_FREQ)
print("候補出力:", OUT_SUG)
