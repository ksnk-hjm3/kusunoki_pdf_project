import os
import logging
import traceback
from flask import Flask, request, abort, jsonify

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Flask app and logging
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Read environment variables by name
# Do NOT hardcode tokens here. Set these in Render Environment.
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_TOKEN:
    app.logger.error("LINE_CHANNEL_ACCESS_TOKEN is not set")
if not LINE_SECRET:
    app.logger.error("LINE_CHANNEL_SECRET is not set")

line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

# Health endpoint for quick checks
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# Webhook callback endpoint
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

# Register message handler only if handler is initialized
if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        try:
            text = event.message.text
            app.logger.info(f"handle_message called. text={text!r}, reply_token={event.reply_token}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
            app.logger.info("reply_message succeeded")
        except LineBotApiError as e:
            app.logger.error(f"LineBotApiError: {getattr(e, 'status_code', 'N/A')} {getattr(e, 'error', e)}")
            traceback.print_exc()
        except Exception:
            app.logger.exception("Exception in handle_message")
else:
    app.logger.error("LINE handler not initialized; skipping message handler registration")

# Local run entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.logger.info(f"Starting dev server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
