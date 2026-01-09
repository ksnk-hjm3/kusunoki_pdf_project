import csv
from collections import OrderedDict
from pathlib import Path

RAW_CSV = Path("raw_companies.csv")
OUT_CSV = Path("companies_master.csv")


def infer_industry(row):
    kw = (row.get("medical_keywords") or "").replace(" ", "").replace("　", "")
    domain = (row.get("medical_domains") or "").strip()
    text = kw + domain

    if "医療機器" in text or "検査" in text or "画像" in text:
        return "医療機器メーカー"
    if "製薬" in text or "医薬" in text or "バイオ" in text:
        return "製薬・バイオ"
    if "オンライン" in text or "AI" in text or "DX" in text or "データ" in text:
        return "医療IT・医療データ"
    if "介護" in text or "福祉" in text or "在宅" in text:
        return "介護・福祉"
    if "卸" in text or "流通" in text:
        return "医療卸・流通"
    if "物流" in text or "配送" in text:
        return "医療物流"
    if "建設" in text or "施設" in text:
        return "医療施設・建設"
    if "衛生" in text or "感染" in text:
        return "衛生・感染対策"
    if "栄養" in text or "健康食品" in text or "サプリ" in text:
        return "ヘルスケア食品・栄養"
    if "フィットネス" in text or "スポーツ" in text:
        return "フィットネス・健康サービス"
    if "出版" in text or "メディア" in text or "ニュース" in text:
        return "医療メディア・出版"
    if "教育" in text or "研修" in text:
        return "教育・研修"

    if domain:
        return domain

    return "その他医療関連"


def build_short_description(name, industry, row):
    if industry == "医療機器メーカー":
        return "医療機器の開発・製造を行い、医療現場で使われる製品を提供しています。"
    if industry == "製薬・バイオ":
        return "医薬品やバイオ製品の研究開発・製造を行い、治療に用いられる薬を提供しています。"
    if industry == "医療IT・医療データ":
        return "医療×IT領域でシステムやデータサービスを提供し、医療現場の業務効率化を支援しています。"
    if industry == "介護・福祉":
        return "介護・福祉サービスを提供し、高齢者支援や在宅ケアの現場に関わる事業を展開しています。"
    if industry == "医療卸・流通":
        return "医薬品や医療機器の流通を担い、医療機関への安定供給を支える卸企業です。"
    if industry == "医療物流":
        return "医薬品や医療機器の輸送・保管を行い、医療機関を支える物流インフラを提供しています。"
    if industry == "医療施設・建設":
        return "医療施設の建設・整備に関わり、病院やクリニックのインフラを支える企業です。"
    if industry == "衛生・感染対策":
        return "衛生用品や感染対策製品を扱い、医療現場や生活の衛生管理を支える製品を提供しています。"
    if industry == "ヘルスケア食品・栄養":
        return "健康食品や栄養関連製品を展開し、日常生活からの健康づくりを支援しています。"
    if industry == "フィットネス・健康サービス":
        return "フィットネスや運動サービスを提供し、生活者の健康維持や体力向上を支援しています。"
    if industry == "医療メディア・出版":
        return "医療・看護・介護分野の情報発信や出版を行い、医療者向けの学習基盤を提供しています。"
    if industry == "教育・研修":
        return "医療・看護分野の教育や研修サービスを提供し、専門職の学びを支援しています。"

    return "医療・ヘルスケア分野に関連する事業を展開し、医療や生活者の健康を支援する企業です。"


def main():
    # ★ UTF-8 with BOM を正しく読む
    with RAW_CSV.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    unique = OrderedDict()
    for row in rows:
        name = (row.get("company_name") or "").strip()
        if not name or name.lower() == "company_name":
            continue
        if name not in unique:
            unique[name] = row

    print(f"元データ行数: {len(rows)}")
    print(f"重複除去後の企業数: {len(unique)}")

    fieldnames = [
        "company_id",
        "company_name",
        "short_description",
        "medical_relevance_score",
        "side_job_fit_score",
        "career_shift_fit_score",
        "hybrid_fit_score",
        "industry",
        "work_style",
        "risk_level",
        "learning_growth_score",
        "target_background",
        "note_for_coach",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, (name, row) in enumerate(unique.items(), start=1):
            industry = infer_industry(row)
            short_desc = build_short_description(name, industry, row)

            score_raw = row.get("total_medical_score") or row.get("medical_keyword_count") or "0"
            try:
                score = int(score_raw)
            except:
                score = 0

            out_row = {
                "company_id": idx,
                "company_name": name,
                "short_description": short_desc,
                "medical_relevance_score": score,
                "side_job_fit_score": "",
                "career_shift_fit_score": "",
                "hybrid_fit_score": "",
                "industry": industry,
                "work_style": "",
                "risk_level": "",
                "learning_growth_score": "",
                "target_background": "",
                "note_for_coach": "",
            }
            writer.writerow(out_row)

    print(f"書き出し完了: {OUT_CSV}")


if __name__ == "__main__":
    main()
