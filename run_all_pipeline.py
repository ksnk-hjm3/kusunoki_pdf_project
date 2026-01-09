# run_all_pipeline.py
# 一回実行でデータ取り込み→候補生成→自動適用→最終化まで行うパイプライン
import csv, shutil, sys, os
from pathlib import Path
from collections import Counter

ROOT = Path.cwd()
BACKUP_DIR = ROOT / "backup_before_run"
BACKUP_DIR.mkdir(exist_ok=True)

# file names
RAW1 = ROOT / "companies_master_raw.csv"
RAW2 = ROOT / "companies_master_final.csv"
OTHERS = ROOT / "others_companies.csv"
TOP100 = ROOT / "top100_by_score.csv"
TEMPLATE = ROOT / "manual_industry_map_template.csv"
SUGGEST = ROOT / "manual_industry_map_suggestions.csv"
KEYWORD_FREQ = ROOT / "keyword_frequency.csv"
AUTO_MAPPED = ROOT / "companies_master_final_auto_mapped_v2.csv"
FINAL = ROOT / "companies_master_final.csv"

def backup(p):
    if p.exists():
        dst = BACKUP_DIR / (p.name + ".bak")
        shutil.copy(p, dst)

def read_csv(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# 0 backup
for p in [OTHERS, TOP100, TEMPLATE, SUGGEST, KEYWORD_FREQ, AUTO_MAPPED, FINAL, RAW2]:
    backup(p)

# 1 choose source master
if RAW1.exists():
    IN_MASTER = RAW1
elif RAW2.exists():
    IN_MASTER = RAW2
else:
    print("INFO: companies_master_raw.csv / companies_master_final.csv が見つかりません。")
    if (ROOT / "others_companies.csv").exists():
        print("INFO: others_companies.csv を元に処理を進めます。")
        IN_MASTER = ROOT / "others_companies.csv"
    else:
        print("ERROR: 元データが見つかりません。companies_master_raw.csv を用意してください。")
        sys.exit(1)

rows = read_csv(IN_MASTER)
if not rows:
    print("ERROR: 入力ファイルが空です。")
    sys.exit(1)

# ensure numeric score field exists
for r in rows:
    if r.get("medical_relevance_score") is None:
        r["medical_relevance_score"] = "0"

# 2 split top100 and others
sorted_rows = sorted(rows, key=lambda x: int(x.get("medical_relevance_score") or 0), reverse=True)
top100 = sorted_rows[:100]
others = sorted_rows[100:]
write_csv(TOP100, top100, fieldnames=top100[0].keys())
if others:
    write_csv(OTHERS, others, fieldnames=others[0].keys())
else:
    write_csv(OTHERS, [], fieldnames=rows[0].keys())
print("Step 1: top100 and others generated")

# 3 ensure manual template exists
if not TEMPLATE.exists():
    with TEMPLATE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company_id","company_name","force_industry"])
    print("Step 2: manual template created (empty)")

# 4 keyword map and suggestion generation
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

def suggest(text):
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

all_inputs = top100 + others
sug_rows = []
freq = Counter()
for r in all_inputs:
    text = " ".join([r.get("company_name",""), r.get("short_description","") or "", r.get("raw_medical_keywords","") or "", r.get("raw_medical_domains","") or ""])
    suggested, conf = suggest(text)
    sug_rows.append({
        "company_id": r.get("company_id",""),
        "company_name": r.get("company_name",""),
        "suggested_industry": suggested,
        "confidence": conf,
        "note": ""
    })
    for token in (r.get("raw_medical_keywords") or "").replace(';',',').split(','):
        t = token.strip()
        if t:
            freq[t] += 1

write_csv(SUGGEST, sug_rows, fieldnames=["company_id","company_name","suggested_industry","confidence","note"])
with KEYWORD_FREQ.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["token","count"])
    for tok, cnt in freq.most_common():
        w.writerow([tok, cnt])
print("Step 3: suggestions and keyword frequency written")

# 5 load manual map to respect manual overrides
manual_map = {}
if TEMPLATE.exists():
    for r in read_csv(TEMPLATE):
        cid = (r.get("company_id") or "").strip()
        if cid and r.get("force_industry"):
            manual_map[cid] = r.get("force_industry").strip()

# 6 apply high-confidence suggestions and manual map
auto_rows = []
for r in all_inputs:
    cid = r.get("company_id","")
    if cid in manual_map:
        r["industry"] = manual_map[cid]
    else:
        s = next((x for x in sug_rows if x["company_id"]==cid), None)
        if s and float(s.get("confidence") or 0) >= 0.8 and s.get("suggested_industry"):
            r["industry"] = s["suggested_industry"]
    auto_rows.append(r)

write_csv(AUTO_MAPPED, auto_rows, fieldnames=auto_rows[0].keys())
print("Step 4: auto-mapped intermediate file created")

# 7 finalize scores and descriptions
def recompute(ms, industry):
    try:
        ms = int(ms)
    except:
        ms = 0
    if ms >= 85:
        s,c,lg = 90,30,80
    elif ms >= 65:
        s,c,lg = 75,40,65
    elif ms >= 40:
        s,c,lg = 60,60,50
    elif ms >= 15:
        s,c,lg = 45,75,40
    else:
        s,c,lg = 25,85,30
    h = int((s+c)/2)
    base = 45
    if "医療機器" in (industry or ""): base = 40
    if "製薬" in (industry or "") or "バイオ" in (industry or ""): base = 50
    if "医療IT" in (industry or ""): base = 30
    if ms >= 80: base -= 10
    if ms <= 10: base += 10
    rl = max(10, min(90, base))
    return s,c,h,lg,rl

final_rows = []
for r in auto_rows:
    ms = r.get("medical_relevance_score") or 0
    industry = r.get("industry") or ""
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
    if not r.get("short_description") or len(r.get("short_description",""))<30:
        tpl = {
            "医療機器メーカー":"医療機器の開発・製造を行い、医療現場で使われる製品を提供しています。",
            "製薬・バイオ":"医薬品やバイオ製品の研究開発・製造を行い、治療に用いられる薬を提供しています。",
            "医療IT・医療データ":"医療×ITでシステムやデータサービスを提供し、現場の効率化を支援します。",
            "介護・福祉":"介護・福祉サービスを提供し、高齢者支援や在宅ケアを行っています。"
        }.get(industry)
        if tpl:
            r["short_description"] = tpl
    final_rows.append(r)

write_csv(FINAL, final_rows, fieldnames=final_rows[0].keys())
print("Step 5: final file written:", FINAL)

# 8 summary
cnt = Counter([r.get("industry") or "その他" for r in final_rows])
scores = [int(r.get("medical_relevance_score") or 0) for r in final_rows]
print("Summary total rows:", sum(cnt.values()))
print("Top industries:")
for k,v in cnt.most_common(10):
    print(k, v)
print("Average medical_relevance_score:", sum(scores)/len(scores) if scores else 0)
print("All outputs written. Manual template respected if present. Edit manual_industry_map_template.csv and re-run to override.")
