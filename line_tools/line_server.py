import os
import logging
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 環境変数取得
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# 環境変数がない場合はLINE機能を無効化してログに残す
if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    logger.warning("LINE_CHANNEL_SECRET or LINE_CHANNEL_ACCESS_TOKEN is not set. LINE features disabled.")
    line_bot_api = None
    handler = None
else:
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/callback", methods=["POST"])
def callback():
    if not handler or not line_bot_api:
        logger.error("Webhook called but LINE is not configured")
        return "LINE not configured", 500

    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature for request: %s", body[:200])
        return "Invalid signature", 400
    except Exception:
        logger.exception("Unhandled exception in handler")
        return "Server error", 500

    return "OK", 200

# LINE メッセージハンドラ
if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        try:
            text = event.message.text
            reply = f"受け取りました: {text}"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        except Exception:
            logger.exception("Failed to reply to message")

# 直接実行用（デバッグや Procfile を python に切り替えた場合に必要）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting Flask dev server on port %d", port)
    app.run(host="0.0.0.0", port=port)
