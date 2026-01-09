import requests
from bs4 import BeautifulSoup

# ============================
# フェーズ4-1：医療系キーワード辞書
# ============================

MEDICAL_KEYWORDS = [
    # 医療一般
    "医療", "医療現場", "医療従事者", "医療機関", "医療知識", "医療経験",
    "臨床", "臨床現場", "患者", "病院", "クリニック", "看護", "介護", "福祉",
    "ヘルスケア", "メディカル",

    # 医療DX / 医療SaaS
    "医療DX", "医療データ", "医療情報", "電子カルテ", "オンライン診療",
    "医療システム", "医療ソリューション", "医療IT", "医療SaaS",

    # 医療機器
    "医療機器", "デバイス", "手術", "検査", "診断", "画像診断", "バイタル",
    "臨床工学", "医療材料",

    # 医療職歓迎文脈
    "医療現場の課題", "医療知識を活かす", "医療経験を歓迎",
    "医療従事者とのコミュニケーション", "医療機関への提案",
    "医療現場の理解", "医療業界経験者歓迎"
]


def calculate_medical_score(text):
    hits = [kw for kw in MEDICAL_KEYWORDS if kw in text]
    count = len(hits)

    if count <= 1:
        score = 1
    elif count <= 4:
        score = 2
    elif count <= 8:
        score = 3
    elif count <= 14:
        score = 4
    else:
        score = 5

    return hits, count, score


# ============================
# フェーズ4-2：医療領域分類辞書
# ============================

MEDICAL_DOMAINS = {
    "医療機器メーカー": [
        "医療機器", "デバイス", "手術", "検査", "診断", "画像診断",
        "バイタル", "臨床工学", "医療材料", "手術支援", "モニタリング"
    ],
    "医療SaaS・医療DX": [
        "医療DX", "電子カルテ", "オンライン診療", "医療システム",
        "医療ソリューション", "医療IT", "医療SaaS", "医療データ",
        "医療情報", "クラウド", "プラットフォーム"
    ],
    "介護・福祉": [
        "介護", "福祉", "高齢者", "施設", "ケア", "介護支援",
        "介護サービス", "介護現場"
    ],
    "臨床開発（CRO）": [
        "治験", "臨床試験", "CRA", "CRC", "GCP", "医薬品開発", "臨床研究"
    ],
    "医療コンサル": [
        "コンサル", "課題解決", "医療経営", "医療機関支援",
        "医療戦略", "業務改善"
    ],
    "医療データ・AI": [
        "医療データ", "AI", "機械学習", "データ分析",
        "医療統計", "予測モデル"
    ],
    "医療人材・医療メディア": [
        "医療人材", "医療メディア", "求人", "キャリア", "医療情報発信"
    ]
}


def classify_medical_domain(text):
    domain_scores = {}

    for domain, keywords in MEDICAL_DOMAINS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            domain_scores[domain] = count

    if not domain_scores:
        return [], {}

    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
    top_score = sorted_domains[0][1]
    top_domains = [d for d, s in sorted_domains if s == top_score]

    return top_domains, domain_scores


# ============================
# フェーズ4-3：医療職が活かせる職種辞書
# ============================

MEDICAL_ROLE_KEYWORDS = {
    "医療機関向け職種": [
        "カスタマーサクセス", "CS", "導入支援", "導入コンサル", "導入エンジニア",
        "フィールドエンジニア", "フィールドサポート", "医療機関向け営業",
        "医療営業", "医療機器営業", "クリニカルスペシャリスト",
        "臨床サポート", "臨床導入", "臨床アドバイザー"
    ],
    "医療SaaS・DX職種": [
        "カスタマーサクセス", "オンボーディング", "サポートエンジニア",
        "プロダクトサポート", "QA", "PM", "医療データアナリスト"
    ],
    "医療機器メーカー職種": [
        "フィールドエンジニア", "サービスエンジニア", "テクニカルサポート",
        "臨床工学技士歓迎", "医療機器インストラクター"
    ],
    "介護・福祉職種": [
        "施設長", "生活相談員", "ケアマネ", "介護支援専門員", "介護コーディネーター"
    ],
    "医療コンサル職種": [
        "コンサルタント", "医療経営コンサル", "業務改善コンサル", "医療機関支援"
    ]
}


def extract_medical_roles(text):
    matched_roles = []

    for category, keywords in MEDICAL_ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matched_roles.append(kw)

    return list(dict.fromkeys(matched_roles))


# ============================
# フェーズ4-4：総合スコア
# ============================

MEDICAL_DOMAIN_SCORE = {
    "医療機器メーカー": 3,
    "医療SaaS・医療DX": 3,
    "介護・福祉": 2,
    "臨床開発（CRO）": 3,
    "医療コンサル": 2,
    "医療データ・AI": 3,
    "医療人材・医療メディア": 1
}


def calculate_role_score(medical_roles):
    count = len(medical_roles)
    if count == 0:
        return 0
    elif count == 1:
        return 1
    elif count == 2:
        return 2
    elif count == 3:
        return 3
    elif count == 4:
        return 4
    else:
        return 5


def calculate_total_score(medical_score, domains, medical_roles):
    domain_score = 0
    for d in domains:
        domain_score = max(domain_score, MEDICAL_DOMAIN_SCORE.get(d, 0))

    role_score = calculate_role_score(medical_roles)

    total = (
        medical_score * 15 +
        domain_score * 10 +
        role_score * 12
    )

    return total


# ============================
# メイン関数：採用ページ解析
# ============================

def parse_recruit_page(url):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text
    except:
        html = ""

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    medical_hits, medical_count, medical_score = calculate_medical_score(text)
    domains, domain_scores = classify_medical_domain(text)
    medical_roles = extract_medical_roles(text)

    total_score = calculate_total_score(
        medical_score,
        domains,
        medical_roles
    )

    return {
        "medical_keywords": ",".join(medical_hits),
        "medical_keyword_count": medical_count,
        "medical_score": medical_score,
        "medical_domains": ",".join(domains),
        "medical_domain_scores": str(domain_scores),
        "medical_roles": ",".join(medical_roles),
        "total_medical_score": total_score
    }
