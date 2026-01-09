# run_pipeline.py
# ------------------------------------------------------------
# 企業データ処理の全工程を一回の実行で完結させる完全版パイプライン
# ------------------------------------------------------------
import csv, shutil, sys
from pathlib import Path
from collections import Counter

ROOT = Path.cwd()
BACKUP = ROOT / "backup_before_run"
BACKUP.mkdir(exist_ok=True)

# 入力候補
RAW1 = ROOT / "companies_master_raw.csv"
RAW2 = ROOT / "companies_master_final.csv"

# 出力ファイル
TOP100 = ROOT / "top100_by_score.csv"
OTHERS = ROOT / "others_companies.csv"
TEMPLATE = ROOT / "manual_industry_map_template.csv"
SUGGEST = ROOT / "manual_industry_map_suggestions.csv"
KEYWORD_FREQ = ROOT / "keyword_frequency.csv"
AUTO = ROOT / "companies_master_auto.csv"
FINAL = ROOT / "companies_master_final.csv"

# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------
def backup(p):
    if p.exists():
        shutil.copy(p, BACKUP / (p.name + ".bak"))

def read_csv(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ------------------------------------------------------------
# 1. 元データの決定
# ------------------------------------------------------------
if RAW1.exists():
    SRC = RAW1
elif RAW2.exists():
    SRC = RAW2
else:
    print("ERROR: companies_master_raw.csv または companies_master_final.csv を置いてください。")
    sys.exit(1)

rows = read_csv(SRC)
if not rows:
    print("ERROR: 入力ファイルが空です。")
    sys.exit(1)

# バックアップ
for p in [TOP100, OTHERS, TEMPLATE, SUGGEST, KEYWORD_FREQ, AUTO, FINAL]:
    backup(p)

# medical_relevance_score を整数化
for r in rows:
    r["medical_relevance_score"] = r.get("medical_relevance_score") or "0"

# ------------------------------------------------------------
# 2. top100 / others 分割
# ------------------------------------------------------------
sorted_rows = sorted(rows, key=lambda x: int(x["medical_relevance_score"]), reverse=True)
top100 = sorted_rows[:100]
others = sorted_rows[100:]

write_csv(TOP100, top100, fieldnames=top100[0].keys())
write_csv(OTHERS, others, fieldnames=others[0].keys())

print("Step 1: top100 / others 生成完了")

# ------------------------------------------------------------
# 3. manual template がなければ作成
# ------------------------------------------------------------
if not TEMPLATE.exists():
    with TEMPLATE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company_id", "company_name", "force_industry"])
    print("Step 2: manual template 新規作成")

# ------------------------------------------------------------
# 4. キーワード解析 & 自動候補生成
# ------------------------------------------------------------
KEYWORD_MAP = {
    "介護":"介護・福祉","看護":"介護・福祉","在宅":"介護・福祉",
    "検査":"医療機器メーカー","診断":"医療機器メーカー","画像":"医療機器メーカー","医療機器":"医療機器メーカー",
    "医療データ":"医療IT・医療データ","医療情報":"医療IT・医療データ","医療saas":"医療IT・医療データ","ai":"医療IT・医療データ",
    "製薬":"製薬・バイオ","バイオ":"製薬・バイオ","薬":"製薬・バイオ",
    "栄養":"ヘルスケア食品・栄養","サプリ":"ヘルスケア食品・栄養",
    "流通":"医療卸・流通","卸":"医療卸・流通",
    "物流":"医療物流","配送":"医療物流",
    "出版":"医療メディア・出版","メディア":"医療メディア・出版",
    "教育":"教育・研修","研修":"教育・研修",
    "フィットネス":"フィットネス・健康サービス","スポーツ":"フィットネス・健康サービス"
}

def suggest_industry(text):
    t = (text or "").lower()
    hits = []
    for k,v in KEYWORD_MAP.items():
        if k in t:
            hits.append(v)
    if not hits:
        return "", 0.0
    cand = Counter(hits).most_common(1)[0][0]
    conf = min(0.95, 0.4 + 0.15 * len(hits))
    return cand, round(conf,2)

all_rows = top100 + others
sug_list = []
freq = Counter()

for r in all_rows:
    text = " ".join([
        r.get("company_name",""),
        r.get("short_description","") or "",
        r.get("raw_medical_keywords","") or "",
        r.get("raw_medical_domains","") or ""
    ])
    sug, conf = suggest_industry(text)
    sug_list.append({
        "company_id": r.get("company_id",""),
        "company_name": r.get("company_name",""),
        "suggested_industry": sug,
        "confidence": conf,
        "note": ""
    })
    for token in (r.get("raw_medical_keywords") or "").replace(";",",").split(","):
        t = token.strip()
        if t:
            freq[t] += 1

write_csv(SUGGEST, sug_list, fieldnames=["company_id","company_name","suggested_industry","confidence","note"])

with KEYWORD_FREQ.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["token","count"])
    for tok,cnt in freq.most_common():
        w.writerow([tok,cnt])

print("Step 3: キーワード解析 & 自動候補生成完了")

# ------------------------------------------------------------
# 5. manual map 読み込み
# ------------------------------------------------------------
manual_map = {}
if TEMPLATE.exists():
    for r in read_csv(TEMPLATE):
        cid = (r.get("company_id") or "").strip()
        if cid and r.get("force_industry"):
            manual_map[cid] = r["force_industry"].strip()

# ------------------------------------------------------------
# 6. 自動分類（高信頼 + manual override）
# ------------------------------------------------------------
auto_rows = []
for r in all_rows:
    cid = r.get("company_id","")
    if cid in manual_map:
        r["industry"] = manual_map[cid]
    else:
        s = next((x for x in sug_list if x["company_id"]==cid), None)
        if s and float(s["confidence"]) >= 0.8 and s["suggested_industry"]:
            r["industry"] = s["suggested_industry"]
    auto_rows.append(r)

write_csv(AUTO, auto_rows, fieldnames=auto_rows[0].keys())
print("Step 4: 自動分類完了")

# ------------------------------------------------------------
# 7. スコア再計算 & short_description 補完
# ------------------------------------------------------------
def recompute(ms, industry):
    ms = int(ms)
    if ms >= 85: s,c,lg = 90,30,80
    elif ms >= 65: s,c,lg = 75,40,65
    elif ms >= 40: s,c,lg = 60,60,50
    elif ms >= 15: s,c,lg = 45,75,40
    else: s,c,lg = 25,85,30
    h = (s+c)//2
    base = 45
    if "医療機器" in industry: base = 40
    if "製薬" in industry or "バイオ" in industry: base = 50
    if "医療IT" in industry: base = 30
    if ms >= 80: base -= 10
    if ms <= 10: base += 10
    rl = max(10, min(90, base))
    return s,c,h,lg,rl

TEMPLATES = {
    "医療機器メーカー":"医療機器の開発・製造を行い、医療現場で使われる製品を提供しています。",
    "製薬・バイオ":"医薬品やバイオ製品の研究開発・製造を行い、治療に用いられる薬を提供しています。",
    "医療IT・医療データ":"医療×ITでシステムやデータサービスを提供し、現場の効率化を支援します。",
    "介護・福祉":"介護・福祉サービスを提供し、高齢者支援や在宅ケアを行っています。"
}

final_rows = []
for r in auto_rows:
    ms = r["medical_relevance_score"]
    industry = r.get("industry","") or ""
    s,c,h,lg,rl = recompute(ms, industry)
    r["side_job_fit_score"] = s
    r["career_shift_fit_score"] = c
    r["hybrid_fit_score"] = h
    r["learning_growth_score"] = lg
    r["risk_level"] = rl

    if "医療IT" in industry:
        r["target_background"] = "ITエンジニア;医療現場経験者;データサイエンティスト"
    elif "医療機器" in industry:
        r["target_background"] = "機械設計;臨床経験者;品質管理"
    elif "製薬" in industry or "バイオ" in industry:
        r["target_background"] = "研究職;臨床開発;薬剤師"
    elif "介護" in industry:
        r["target_background"] = "介護職;看護師;福祉系経験者"
    else:
        r["target_background"] = "医療関連経験者;業界未経験者歓迎"

    sd = r.get("short_description","") or ""
    if len(sd) < 30 and industry in TEMPLATES:
        r["short_description"] = TEMPLATES[industry]

    final_rows.append(r)

write_csv(FINAL, final_rows, fieldnames=final_rows[0].keys())
print("Step 5: 最終ファイル生成完了 → companies_master_final.csv")

# ------------------------------------------------------------
# 8. Summary
# ------------------------------------------------------------
cnt = Counter([r.get("industry") or "その他" for r in final_rows])
scores = [int(r["medical_relevance_score"]) for r in final_rows]

print("\n===== SUMMARY =====")
print("総件数:", len(final_rows))
print("平均 medical_relevance_score:", sum(scores)/len(scores))
print("業界上位10:")
for k,v in cnt.most_common(10):
    print(f"{k}: {v}")
print("====================\n")
