#!/usr/bin/env python3
# select_and_pitch.py
# 一回実行で: 候補抽出 -> 簡易求人チェック -> 上位3社選定 -> 提案ピッチ生成

import csv
import sys
from pathlib import Path
from collections import defaultdict
import requests
from requests.exceptions import RequestException
import time

ROOT = Path.cwd()
INPUT = ROOT / "companies_master_final.csv"
CAND20 = ROOT / "candidates_top20.csv"
CAND20_JOBS = ROOT / "candidates_top20_with_jobs.csv"
FINAL3 = ROOT / "final_3_recommendations.csv"
PITCH = ROOT / "final_3_pitches.txt"

# 設定（必要なら調整）
MIN_MEDICAL_SCORE = 60        # medical_relevance_score の下限
MIN_HYBRID_SCORE = 40         # hybrid_fit_score の下限（候補抽出）
MAX_RISK_LEVEL = 70          # risk_level の上限（候補抽出）
TOP_N_CANDIDATES = 20        # 候補抽出数
TOP_K_FINAL = 3              # 最終選定数
CAREER_PATHS = [             # 企業サイト上の採用ページ候補パス（HEADで確認）
    "/careers", "/jobs", "/recruit", "/recruitment", "/採用", "/recruiters", "/career", "/jobs/positions"
]
HTTP_TIMEOUT = 5             # seconds for HEAD requests
USER_AGENT = "Mozilla/5.0 (compatible; CandidateChecker/1.0)"

def read_csv(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def safe_int(v, default=0):
    try:
        return int(float(v))
    except:
        return default

def check_career_urls(base_url):
    """簡易チェック: base_url があれば CAREER_PATHS を HEAD で試す。
       戻り値: (has_openings_bool, matched_url or '')"""
    if not base_url:
        return False, ""
    # normalize
    if not base_url.startswith("http"):
        base_url = "https://" + base_url.strip().lstrip("/")
    # try base first (some sites have /careers in root)
    candidates = [base_url.rstrip("/")] + [base_url.rstrip("/") + p for p in CAREER_PATHS]
    headers = {"User-Agent": USER_AGENT}
    for url in candidates:
        try:
            # HEAD may be blocked; try GET fallback if HEAD fails
            r = requests.head(url, timeout=HTTP_TIMEOUT, headers=headers, allow_redirects=True)
            if r.status_code == 200:
                return True, url
            # some servers block HEAD; try GET with small timeout
            if r.status_code in (405, 403, 400):
                r2 = requests.get(url, timeout=HTTP_TIMEOUT, headers=headers, allow_redirects=True)
                if r2.status_code == 200:
                    return True, url
        except RequestException:
            # ignore and continue
            continue
    return False, ""

def generate_pitch(row):
    """短いピッチ（3行）を自動生成"""
    name = row.get("company_name","").strip()
    industry = row.get("industry","") or "業界情報なし"
    score = safe_int(row.get("medical_relevance_score",0))
    hybrid = safe_int(row.get("hybrid_fit_score",0))
    risk = safe_int(row.get("risk_level",0))
    reason = []
    reason.append(f"理由: 医療関連性 {score} / ハイブリッド適合 {hybrid}、業界: {industry}。")
    # 強調点
    if "医療IT" in industry:
        reason.append("強み: 医療×IT領域での成長性とデータ利活用の機会が豊富です。")
    elif "医療機器" in industry:
        reason.append("強み: 製品開発・設計領域での専門性を活かせます。")
    elif "介護" in industry:
        reason.append("強み: 実務経験を活かした現場寄りの役割が見込めます。")
    elif "製薬" in industry or "バイオ" in industry:
        reason.append("強み: 研究・臨床開発に関わる専門性が評価されます。")
    else:
        reason.append("強み: 医療領域での汎用的な経験が活かせます。")
    # リスクと次アクション
    next_action = f"次の一手: 企業の採用ページを確認し、募集ポジションが合致するかを確認してください（リスク指標: {risk}）。"
    pitch = f"{name}\n" + "\n".join(reason[:2]) + "\n" + next_action
    return pitch

def main():
    if not INPUT.exists():
        print("ERROR: companies_master_final.csv が見つかりません。プロジェクトルートに配置してください。")
        sys.exit(1)

    rows = read_csv(INPUT)
    # フィルタ条件で候補抽出
    candidates = []
    for r in rows:
        ms = safe_int(r.get("medical_relevance_score",0))
        hy = safe_int(r.get("hybrid_fit_score",0))
        rl = safe_int(r.get("risk_level",0))
        if ms >= MIN_MEDICAL_SCORE and hy >= MIN_HYBRID_SCORE and rl <= MAX_RISK_LEVEL:
            candidates.append(r)
    # スコア順にソート
    candidates_sorted = sorted(candidates, key=lambda x: safe_int(x.get("medical_relevance_score",0)), reverse=True)
    top_candidates = candidates_sorted[:TOP_N_CANDIDATES]
    if not top_candidates:
        print("候補が見つかりませんでした。閾値を下げるかデータを確認してください。")
        sys.exit(0)

    # 書き出し: candidates_top20.csv
    fieldnames = list(top_candidates[0].keys())
    write_csv(CAND20, top_candidates, fieldnames=fieldnames)
    print(f"候補上位 {len(top_candidates)} 件を {CAND20.name} に出力しました。")

    # 簡易求人チェック: company_website または raw_medical_domains を利用
    enriched = []
    for r in top_candidates:
        # try to find a website field; common columns: company_website, website, url, raw_medical_domains
        base = r.get("company_website") or r.get("website") or r.get("url") or r.get("raw_medical_domains") or ""
        # if raw_medical_domains contains comma-separated domains, take first
        if base and "," in base:
            base = base.split(",")[0].strip()
        has_jobs, matched_url = False, ""
        if base:
            has_jobs, matched_url = check_career_urls(base)
            # small delay to be polite
            time.sleep(0.2)
        r2 = dict(r)
        r2["has_open_jobs"] = "1" if has_jobs else "0"
        r2["matched_jobs_url"] = matched_url
        enriched.append(r2)

    # write candidates with job check
    fieldnames2 = list(enriched[0].keys())
    write_csv(CAND20_JOBS, enriched, fieldnames=fieldnames2)
    print(f"求人チェック結果を {CAND20_JOBS.name} に出力しました。")

    # 最終選定: 採用シグナル優先 -> medical_relevance_score 降順
    with_jobs = [r for r in enriched if r.get("has_open_jobs") == "1"]
    without_jobs = [r for r in enriched if r.get("has_open_jobs") != "1"]
    ordered = sorted(with_jobs, key=lambda x: safe_int(x.get("medical_relevance_score",0)), reverse=True) + \
              sorted(without_jobs, key=lambda x: safe_int(x.get("medical_relevance_score",0)), reverse=True)
    final3 = ordered[:TOP_K_FINAL]
    if not final3:
        print("最終候補が見つかりません。")
        sys.exit(0)

    # 出力 final_3_recommendations.csv
    write_csv(FINAL3, final3, fieldnames=list(final3[0].keys()))
    print(f"最終3社を {FINAL3.name} に出力しました。")

    # ピッチ生成
    with PITCH.open("w", encoding="utf-8") as f:
        for r in final3:
            pitch = generate_pitch(r)
            f.write(pitch + "\n\n" + ("-"*40) + "\n\n")
    print(f"各社の短いピッチを {PITCH.name} に出力しました。")

    print("完了: final_3_recommendations.csv と final_3_pitches.txt を確認してください。")

if __name__ == "__main__":
    main()
