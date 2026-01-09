import csv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from diagnosis.diagnosis_core import diagnose_thinking_pattern
from diagnosis.questions import questions

app = Flask(__name__)

# --- LINE 設定 ---
LINE_CHANNEL_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
LINE_CHANNEL_SECRET = "YOUR_CHANNEL_SECRET"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- ユーザー回答を一時保存 ---
user_answers = {}  # {user_id: {1:1, 2:0, ...}}


# ---------------------------
# CSV 読み込み
# ---------------------------
def load_companies(csv_path="data/companies_master.csv"):
    companies = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 数値項目を int に変換
                for key in [
                    "medical_relevance_score",
                    "side_job_fit_score",
                    "career_shift_fit_score",
                    "hybrid_fit_score",
                ]:
                    if key in row and row[key].isdigit():
                        row[key] = int(row[key])
                    else:
                        row[key] = 0
                companies.append(row)
    except Exception as e:
        print("CSV読み込みエラー:", e)
    return companies


# ---------------------------
# 診断結果に応じた企業抽出
# ---------------------------
def pick_companies(thinking_type, companies):
    # thinking_type に応じて使用スコアを決定
    if thinking_type == "side_job":
        score_key = "side_job_fit_score"
    elif thinking_type == "career_shift":
        score_key = "career_shift_fit_score"
    elif thinking_type == "hybrid":
        score_key = "hybrid_fit_score"
    else:  # undifferentiated
        score_key = "medical_relevance_score"

    # スコア順に並べて上位3社を返す
    sorted_companies = sorted(
        companies,
        key=lambda c: c.get(score_key, 0),
        reverse=True,
    )
    return sorted_companies[:3]


# ---------------------------
# Webhook エンドポイント
# ---------------------------
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ---------------------------
# メッセージ受信
# ---------------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # --- 診断開始 ---
    if text == "診断":
        user_answers[user_id] = {}
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("質問1：" + questions[1] + "（はい / いいえ）")
        )
        return

    # --- 回答処理 ---
    if user_id in user_answers:
        answers = user_answers[user_id]
        q_num = len(answers) + 1

        # 回答を 0/1 に変換
        if text == "はい":
            answers[q_num] = 1
        elif text == "いいえ":
            answers[q_num] = 0
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("「はい」か「いいえ」で答えてください。")
            )
            return

        # 次の質問へ
        if q_num < 20:
            next_q = q_num + 1
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(f"質問{next_q}：" + questions[next_q] + "（はい / いいえ）")
            )
            return

        # --- 20問終了 → 診断実行 ---
        result = diagnose_thinking_pattern(answers)
        thinking_type = result["thinking_type"]

        # --- 企業リスト読み込み ---
        companies = load_companies()

        # --- 企業抽出 ---
        recommended = pick_companies(thinking_type, companies)

        # --- メッセージ生成（冷たい表現） ---
        header = "あなたのアンケートを基に関連領域で一般的に知られている企業、これはほんの一部です。\n"

        message = header
        for i, c in enumerate(recommended, start=1):
            message += f"\n{i}. {c['company_name']}\n　{c['short_description']}\n"

        # --- LINE返信 ---
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(message)
        )

        # 診断データ削除
        del user_answers[user_id]
        return


if __name__ == "__main__":
    app.run(port=8000)
