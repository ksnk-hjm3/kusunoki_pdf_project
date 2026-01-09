import csv
import time

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# ============================
# 設定
# ============================
INPUT_CSV = "medical_company_master.csv"
OUTPUT_CSV = "company_recruit_pages.csv"

# 採用ページ候補として拾うキーワード
RECRUIT_KEYWORDS = [
    "採用", "リクルート", "キャリア", "Careers", "Recruit",
    "求人", "募集要項", "採用情報", "新卒採用", "中途採用"
]


# ============================
# 企業マスター読み込み
# ============================
def load_company_master():
    companies = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append({
                "company_name": row.get("company_name", "").strip(),
                "official_url": row.get("official_url", "").strip()
            })
    print(f"[INFO] Loaded {len(companies)} companies from master")
    return companies


# ============================
# HTML取得（requests優先、失敗したらSelenium）
# ============================
def fetch_html(url, driver=None, timeout=15):
    # まず requests でトライ（静的ページ向き）
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.ok and "text/html" in resp.headers.get("Content-Type", ""):
            return resp.text
    except Exception as e:
        print(f"[WARN] requests failed for {url}: {e}")

    # Selenium が使える場合のみ fallback
    if driver is None:
        return None

    try:
        driver.get(url)
        time.sleep(2)
        return driver.page_source
    except Exception as e:
        print(f"[WARN] selenium failed for {url}: {e}")
        return None


# ============================
# 採用ページ候補リンクの探索
# ============================
def find_recruit_page(official_url, driver=None):
    html = fetch_html(official_url, driver=driver)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")

    candidates = []

    for a in links:
        text = (a.get_text() or "").strip()
        href = (a.get("href") or "").strip()

        if not href:
            continue

        # テキストと href の両方を対象にキーワードマッチ
        target_str = text + " " + href

        if any(k in target_str for k in RECRUIT_KEYWORDS):
            full_url = urljoin(official_url, href)
            candidates.append((text, full_url))

    if not candidates:
        return None

    # 一旦、最初の候補を採用（必要ならスコアリングも可能）
    best_text, best_url = candidates[0]
    print(f"[DEBUG] Recruit candidate: {best_text} -> {best_url}")
    return best_url


# ============================
# 結果保存
# ============================
def save_results(rows):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "company_name",
            "official_url",
            "recruit_url",
            "recruit_found"
        ])
        for r in rows:
            writer.writerow([
                r["company_name"],
                r.get("official_url", ""),
                r.get("recruit_url", ""),
                r.get("recruit_found", False),
            ])
    print(f"[INFO] Saved: {OUTPUT_CSV}")


# ============================
# メイン処理
# ============================
def main():
    print("=== 採用ページ探索 START ===")

    companies = load_company_master()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)

    results = []

    for c in companies:
        name = c["company_name"]
        url = c["official_url"]

        print(f"\n[INFO] Processing: {name}")

        if not url:
            print(f"[WARN] official_url is empty for {name}, skip")
            results.append({
                "company_name": name,
                "official_url": "",
                "recruit_url": "",
                "recruit_found": False
            })
            continue

        recruit_url = find_recruit_page(url, driver=driver)

        if recruit_url:
            print(f"[INFO] Recruit page found for {name}: {recruit_url}")
            results.append({
                "company_name": name,
                "official_url": url,
                "recruit_url": recruit_url,
                "recruit_found": True
            })
        else:
            print(f"[INFO] Recruit page NOT found for {name}")
            results.append({
                "company_name": name,
                "official_url": url,
                "recruit_url": "",
                "recruit_found": False
            })

    driver.quit()
    save_results(results)
    print("[INFO] Completed.")


if __name__ == "__main__":
    main()
