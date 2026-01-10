# line_tools/line_server.py
import os
import logging
import traceback
from flask import Flask, request, jsonify, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("line_server")

# Read environment variables
LINE_TOKEN = os.environ.get("JyteEO/ShmBaNHkrIpNQEGJRNcd5YqrKZUotk3RlAPOVQiFcIVKS4Fgqgb5uoWBwsZyyNOGdJwt7VbiVEXKW0M5ocqS2o1JgctRehZUTyOKpkj/f074yUaQn04FEnG+qRSrfWaUJdlTa6mJ1MSYhfQdB04t89/1O/w1cDnyilFU=")
LINE_SECRET = os.environ.get("dc3b3c9a822fa38a14dfc9dfc1dfbcf7")

# Initialize LINE SDK objects if env vars present
line_bot_api = LineBotApi(LINE_TOKEN) if LINE_TOKEN else None
handler = WebhookHandler(LINE_SECRET) if LINE_SECRET else None

app = Flask("line_server")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    app.logger.info(f"Callback received length={len(body)} signature_present={'yes' if signature else 'no'}")

    if handler is None or line_bot_api is None:
        app.logger.error("LINE SDK not initialized due to missing env vars")
        return jsonify({}), 200

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature - signature mismatch")
        abort(400)
    except Exception:
        app.logger.error("Unhandled exception in handler.handle:")
        traceback.print_exc()
        abort(500)

    return jsonify({}), 200


# Register message handler only if handler is initialized
if handler is not None:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        try:
            text = event.message.text if event.message and hasattr(event.message, "text") else ""
            app.logger.info(f"handle_message called. text={text!r}, reply_token={event.reply_token}")
            # Echo back the received text
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
            app.logger.info("reply_message succeeded")
        except Exception:
            app.logger.error("Failed to reply message:")
            traceback.print_exc()
else:
    # Fallback handler function to avoid NameError if referenced elsewhere
    def handle_message(event):
        app.logger.error("handle_message called but handler is not initialized")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.logger.info(f"Starting dev server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
