# run_pipeline_full.py
# 一回実行で最初の選定から最終出力まで完結するパイプライン（UTF-8）
import csv, shutil, sys, argparse
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path.cwd()
BACKUP_DIR = ROOT / "backup_before_run"
BACKUP_DIR.mkdir(exist_ok=True)

# 入出力ファイル名（必要ならここを変更）
SRC_RAW = ROOT / "companies_master_raw.csv"
SRC_FINAL = ROOT / "companies_master_final.csv"  # フォールバック
TOP100 = ROOT / "top100_by_score.csv"
OTHERS = ROOT / "others_companies.csv"
MANUAL_TEMPLATE = ROOT / "manual_industry_map_template.csv"        # 人が編集するテンプレ
MANUAL_PREFILL = ROOT / "manual_industry_map_prefill.csv"          # 自動プリフィル候補（編集用）
SUGGEST = ROOT / "manual_industry_map_suggestions.csv"            # 候補一覧（confidence付き）
KEYWORD_FREQ = ROOT / "keyword_frequency.csv"
AUTO_MAPPED = ROOT / "companies_master_auto.csv"                  # 自動適用中間
FINAL = ROOT / "companies_master_final.csv"                       # 最終出力
AUTO_APPLY_LOG = ROOT / "auto_apply_log.csv"                      # どれを自動適用したかのログ

# 設定: 自動プリフィル閾値（候補をprefillに入れる閾値）と自動適用閾値
PREFILL_CONF_THRESHOLD = 0.6   # この信頼度以上を manual_prefill に書き出す（レビュー用）
AUTO_APPLY_CONF_THRESHOLD = 0.8  # この信頼度以上は自動で industry に適用する

# キーワード→業界マップ（必要ならここを拡張）
KEYWORD_MAP = {
    "介護":"介護・福祉","看護":"介護・福祉","在宅":"介護・福祉",
    "検査":"医療機器メーカー","診断":"医療機器メーカー","画像":"医療機器メーカー","医療機器":"医療機器メーカー","装置":"医療機器メーカー",
    "医療データ":"医療IT・医療データ","医療情報":"医療IT・医療データ","医療saas":"医療IT・医療データ","ai":"医療IT・医療データ",
    "製薬":"製薬・バイオ","医薬":"製薬・バイオ","バイオ":"製薬・バイオ","薬":"製薬・バイオ",
    "栄養":"ヘルスケア食品・栄養","サプリ":"ヘルスケア食品・栄養","健康食品":"ヘルスケア食品・栄養",
    "流通":"医療卸・流通","卸":"医療卸・流通",
    "物流":"医療物流","配送":"医療物流","倉庫":"医療物流",
    "出版":"医療メディア・出版","メディア":"医療メディア・出版","情報発信":"医療メディア・出版",
    "教育":"教育・研修","研修":"教育・研修","スクール":"教育・研修",
    "フィットネス":"フィットネス・健康サービス","スポーツ":"フィットネス・健康サービス"
}

# ヘルパー
def backup_if_exists(p: Path):
    if p.exists():
        dst = BACKUP_DIR / (p.name + ".bak")
        shutil.copy(p, dst)

def read_csv(path: Path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def suggest_industry_from_text(text: str):
    t = (text or "").lower()
    hits = []
    for k,v in KEYWORD_MAP.items():
        if k in t:
            hits.append(v)
    if not hits:
        return "", 0.0, []
    # 最頻出候補を選ぶ
    cand = Counter(hits).most_common(1)[0][0]
    # confidence: ベース0.4 + 0.15 * ヒット数（上限0.95）
    conf = min(0.95, 0.4 + 0.15 * len(hits))
    return cand, round(conf,2), hits

# メイン処理
def run(dry_run=False):
    # 0. 入力ファイル検出（RAW優先、なければFINALをフォールバック）
    if SRC_RAW.exists():
        src = SRC_RAW
    elif SRC_FINAL.exists():
        src = SRC_FINAL
    else:
        print("ERROR: companies_master_raw.csv または companies_master_final.csv をプロジェクトルートに置いてください。")
        sys.exit(1)

    rows = read_csv(src)
    if not rows:
        print("ERROR: 入力ファイルが空です。")
        sys.exit(1)

    # 1. バックアップ（重要ファイル）
    for p in [TOP100, OTHERS, MANUAL_TEMPLATE, MANUAL_PREFILL, SUGGEST, KEYWORD_FREQ, AUTO_MAPPED, FINAL, AUTO_APPLY_LOG]:
        backup_if_exists(p)

    # 2. medical_relevance_score を整備
    for r in rows:
        r["medical_relevance_score"] = r.get("medical_relevance_score") or "0"

    # 3. top100 / others 分割
    sorted_rows = sorted(rows, key=lambda x: int(x.get("medical_relevance_score") or 0), reverse=True)
    top100 = sorted_rows[:100]
    others = sorted_rows[100:]
    write_csv(TOP100, top100, fieldnames=top100[0].keys())
    write_csv(OTHERS, others, fieldnames=others[0].keys())
    print("Step: top100 / others を生成しました。")

    # 4. 候補生成（全件）
    all_rows = top100 + others
    suggestions = []
    token_freq = Counter()
    # token->matched_keywords map for logging
    matched_tokens_map = defaultdict(list)

    for r in all_rows:
        text = " ".join([r.get("company_name","") or "", r.get("short_description","") or "", r.get("raw_medical_keywords","") or "", r.get("raw_medical_domains","") or ""])
        suggested, conf, hits = suggest_industry_from_text(text)
        suggestions.append({
            "company_id": r.get("company_id",""),
            "company_name": r.get("company_name",""),
            "suggested_industry": suggested,
            "confidence": conf,
            "matched_tokens": ";".join(hits),
            "note": ""
        })
        # token frequency（raw_medical_keywords を ; , 両方対応で分割）
        rawk = (r.get("raw_medical_keywords") or "")
        for token in rawk.replace(";",",").split(","):
            t = token.strip()
            if t:
                token_freq[t] += 1
                matched_tokens_map[r.get("company_id","")].append(t)

    write_csv(SUGGEST, suggestions, fieldnames=["company_id","company_name","suggested_industry","confidence","matched_tokens","note"])
    with KEYWORD_FREQ.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["token","count"])
        for tok,cnt in token_freq.most_common():
            w.writerow([tok,cnt])
    print("Step: 自動候補とキーワード頻度を出力しました。")

    # 5. manual template がなければ作成（空テンプレ）
    if not MANUAL_TEMPLATE.exists():
        with MANUAL_TEMPLATE.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["company_id","company_name","force_industry"])
        print("Step: manual_industry_map_template.csv を新規作成しました（空）。")

    # 6. 自動プリフィル（レビュー用ファイル）: confidence >= PREFILL_CONF_THRESHOLD を出力
    prefill_rows = []
    for s in suggestions:
        if s["confidence"] >= PREFILL_CONF_THRESHOLD and s["suggested_industry"]:
            prefill_rows.append({
                "company_id": s["company_id"],
                "company_name": s["company_name"],
                "suggested_industry": s["suggested_industry"],
                "confidence": s["confidence"],
                "matched_tokens": s["matched_tokens"]
            })
    # 書き出し（編集用）
    if prefill_rows:
        write_csv(MANUAL_PREFILL, prefill_rows, fieldnames=["company_id","company_name","suggested_industry","confidence","matched_tokens"])
        print(f"Step: manual_prefill を作成しました（{len(prefill_rows)} 件）。編集して manual_industry_map_template.csv に反映できます。")
    else:
        # 空ファイルを作る
        with MANUAL_PREFILL.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["company_id","company_name","suggested_industry","confidence","matched_tokens"])
        print("Step: manual_prefill は候補なし（空ファイルを作成）。")

    # 7. manual template を読み込み（手動指定を尊重）
    manual_map = {}
    for r in read_csv(MANUAL_TEMPLATE):
        cid = (r.get("company_id") or "").strip()
        if cid and r.get("force_industry"):
            manual_map[cid] = r["force_industry"].strip()

    # 8. 自動適用（confidence >= AUTO_APPLY_CONF_THRESHOLD）と manual override を適用
    auto_applied_log = []
    auto_rows = []
    for r in all_rows:
        cid = r.get("company_id","")
        original_ind = r.get("industry","") or ""
        applied_from = ""
        # manual override優先
        if cid in manual_map:
            r["industry"] = manual_map[cid]
            applied_from = "manual_template"
        else:
            # find suggestion
            s = next((x for x in suggestions if x["company_id"]==cid), None)
            if s and s.get("suggested_industry") and float(s.get("confidence") or 0) >= AUTO_APPLY_CONF_THRESHOLD:
                r["industry"] = s["suggested_industry"]
                applied_from = f"auto_conf_{s['confidence']}"
        auto_rows.append(r)
        if applied_from:
            auto_applied_log.append({
                "company_id": cid,
                "company_name": r.get("company_name",""),
                "applied_from": applied_from,
                "new_industry": r.get("industry",""),
                "original_industry": original_ind,
                "confidence": s["confidence"] if s else ""
            })

    # 9. 中間ファイル出力（自動適用後）
    write_csv(AUTO_MAPPED, auto_rows, fieldnames=auto_rows[0].keys())
    # ログ出力
    if auto_applied_log:
        write_csv(AUTO_APPLY_LOG, auto_applied_log, fieldnames=["company_id","company_name","applied_from","new_industry","original_industry","confidence"])
        print(f"Step: 自動適用ログを出力しました（{len(auto_applied_log)} 件）。")
    else:
        with AUTO_APPLY_LOG.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["company_id","company_name","applied_from","new_industry","original_industry","confidence"])
        print("Step: 自動適用ログは0件（空ファイルを作成）。")

    # 10. スコア再計算と short_description 補完（最終化）
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

    TEMPLATES = {
        "医療機器メーカー":"医療機器の開発・製造を行い、医療現場で使われる製品を提供しています。",
        "製薬・バイオ":"医薬品やバイオ製品の研究開発・製造を行い、治療に用いられる薬を提供しています。",
        "医療IT・医療データ":"医療×ITでシステムやデータサービスを提供し、現場の効率化を支援します。",
        "介護・福祉":"介護・福祉サービスを提供し、高齢者支援や在宅ケアを行っています。"
    }

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
        sd = r.get("short_description","") or ""
        if len(sd) < 30 and industry in TEMPLATES:
            r["short_description"] = TEMPLATES[industry]
        final_rows.append(r)

    # 11. 最終出力（ファイル書き込み）
    write_csv(FINAL, final_rows, fieldnames=final_rows[0].keys())
    print("Step: 最終ファイルを書き出しました ->", FINAL.name)

    # 12. 最終サマリ表示
    cnt = Counter([r.get("industry") or "その他" for r in final_rows])
    scores = [int(r.get("medical_relevance_score") or 0) for r in final_rows]
    print("\n===== SUMMARY =====")
    print("総件数:", len(final_rows))
    print("平均 medical_relevance_score:", round(sum(scores)/len(scores),2) if scores else 0)
    print("業界上位10:")
    for k,v in cnt.most_common(10):
        print(f"{k}: {v}")
    print("====================\n")

    # 13. 実行完了メッセージと次の推奨アクション
    print("完了しました。")
    print("推奨: manual_industry_map_prefill.csv を確認し、必要なら manual_industry_map_template.csv に反映して再実行してください。")
    print("自動適用ログ:", AUTO_APPLY_LOG.name)
    print("候補一覧:", SUGGEST.name)
    print("キーワード頻度:", KEYWORD_FREQ.name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="一発実行パイプライン")
    parser.add_argument("--dry-run", action="store_true", help="ファイル書き出しを行わずログのみ出す（未実装）")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
