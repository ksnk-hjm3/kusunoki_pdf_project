import os
import csv
from typing import Dict, Any

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "companies_master_final.csv")

def load_companies():
    companies = []
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} not found")
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)
    return companies

def compute_top3_from_answers(answers: Dict[str, Any], companies):
    # 実運用ではここにマッチングロジックを入れる
    top = companies[:3]
    lines = ["アンケート結果に基づくおすすめ企業です。"]
    for i, c in enumerate(top, start=1):
        name = c.get("company_name") or c.get("name") or f"company_{i}"
        lines.append(f"{i}. {name}")
    return "\n".join(lines), top

def handle_survey_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    answers = payload.get("answers", {})
    user_id = payload.get("user_id")
    companies = load_companies()
    reply_text, top3 = compute_top3_from_answers(answers, companies)
    return {
        "status": "ok",
        "reply_text": reply_text,
        "top3": top3,
        "user_id": user_id
    }

def send_push_message_if_needed(line_bot_api, result: Dict[str, Any]):
    if not line_bot_api:
        return
    user_id = result.get("user_id")
    if not user_id:
        return
    from linebot.models import TextSendMessage
    text = result.get("reply_text", "")
    # 例外は呼び出し元でログ化する
    line_bot_api.push_message(user_id, TextSendMessage(text=text))
