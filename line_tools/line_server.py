# --- 必要な import がファイル先頭にあることを確認 ---
import os, logging, traceback
from flask import Flask, request, abort, jsonify

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- Flask アプリとログ設定（ファイル先頭付近に置く） ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

LINE_TOKEN = os.environ.get("JyteEO/ShmBaNHkrIpNQEGJRNcd5YqrKZUotk3RlAPOVQiFcIVKS4Fgqgb5uoWBwsZyyNOGdJwt7VbiVEXKW0M5ocqS2o1JgctRehZUTyOKpkj/f074yUaQn04FEnG+qRSrfWaUJdlTa6mJ1MSYhfQdB04t89/1O/w1cDnyilFU=")
LINE_SECRET = os.environ.get("dc3b3c9a822fa38a14dfc9dfc1dfbcf7")

if not LINE_TOKEN:
    app.logger.error("LINE_CHANNEL_ACCESS_TOKEN is not set")
if not LINE_SECRET:
    app.logger.error("LINE_CHANNEL_SECRET is not set")

line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

# --- /callback エンドポイント（既存のものを置き換える） ---
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    app.logger.info(f"Callback received length={len(body)}")
    if handler is None or line_bot_api is None:
        app.logger.error("LINE SDK not initialized due to missing env vars")
        return jsonify({}), 200

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature")
        abort(400)
    except Exception:
        app.logger.error("Unhandled exception in handler.handle:")
        traceback.print_exc()
        abort(500)
    return jsonify({}), 200

# --- メッセージハンドラ（既存のものを置き換える） ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        text = event.message.text
        app.logger.info(f"handle_message called. text={text!r}, reply_token={event.reply_token}")
        # 受け取ったテキストをそのまま返信する例
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
        app.logger.info("reply_message succeeded")
    except LineBotApiError as e:
        app.logger.error(f"LineBotApiError: {getattr(e,'status_code', 'N/A')} {getattr(e,'error', e)}")
        traceback.print_exc()
    except Exception:
        app.logger.error("Exception in handle_message:")
        traceback.print_exc()
