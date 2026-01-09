
import os
import sys
import logging
from flask import Flask, request, jsonify

# プロジェクトルートを sys.path に追加
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from survey_reply_handler import handle_survey_request, send_push_message_if_needed

# LINE SDK
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# 環境変数（Render の Environment に設定）
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
SURVEY_CALLBACK_TOKEN = os.environ.get("SURVEY_CALLBACK_TOKEN")  # 任意

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    app.logger.warning("LINE_CHANNEL_SECRET or LINE_CHANNEL_ACCESS_TOKEN not set. LINE features disabled.")

line_bot_api = None
parser = None
try:
    if LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        parser = WebhookParser(LINE_CHANNEL_SECRET)
except Exception as e:
    app.logger.exception("Failed to init LINE SDK: %s", e)
    line_bot_api = None
    parser = None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# 本番用 /callback（署名検証あり）
@app.route("/callback", methods=["POST"])
def callback():
    if not parser:
        app.logger.error("Webhook received but parser not configured")
        return "server misconfigured", 500

    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature")
        return "invalid signature", 400
    except Exception as e:
        app.logger.exception("Error parsing webhook")
        return "error", 500

    for event in events:
        try:
            if isinstance(event, MessageEvent):
                user_id = getattr(event.source, "user_id", None) or getattr(event.source, "userId", None)
                app.logger.info("LINE message from user_id=%s", user_id)
                # 必要ならここで即時応答や DB 登録などを行う
        except Exception:
            app.logger.exception("Error handling event")

    return "OK", 200

# /survey_callback : アンケート結果を受け取り処理する
@app.route("/survey_callback", methods=["POST"])
def survey_callback():
    # 任意トークンが設定されている場合はチェック（本番推奨）
    if SURVEY_CALLBACK_TOKEN:
        token = request.headers.get("X-SURVEY-TOKEN", "")
        if token != SURVEY_CALLBACK_TOKEN:
            app.logger.warning("Invalid survey token")
            return jsonify({"status": "unauthorized"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        app.logger.exception("Invalid JSON")
        return jsonify({"status": "error", "error": "invalid_json", "detail": str(e)}), 400

    try:
        result = handle_survey_request(payload)
    except Exception as e:
        app.logger.exception("Error handling survey request")
        return jsonify({"status": "error", "error": str(e)}), 500

    # push を試みる（LINE 設定があれば）
    try:
        send_push_message_if_needed(line_bot_api, result)
    except Exception:
        app.logger.exception("Error sending push message (non-fatal)")

    return jsonify(result), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
