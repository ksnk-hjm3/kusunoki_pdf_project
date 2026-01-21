# line_tools/line_server.py
import os
import logging
import traceback
from flask import Flask, request, jsonify, abort, render_template, make_response, send_from_directory

# Optional: LINE SDK imports (only used if env vars are set)
try:
    from linebot import LineBotApi, WebhookHandler
    from linebot.exceptions import InvalidSignatureError
    from linebot.models import MessageEvent, TextMessage, TextSendMessage
except Exception:
    LineBotApi = None
    WebhookHandler = None
    InvalidSignatureError = Exception
    MessageEvent = None
    TextMessage = None
    TextSendMessage = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("line_server")

# Read environment variables (use safe env var names)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LIFF_ID = os.environ.get("LIFF_ID", "YOUR_LIFF_ID_HERE")

# Initialize LINE SDK objects only if env vars are present
line_bot_api = None
handler = None
if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET and LineBotApi and WebhookHandler:
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        handler = WebhookHandler(LINE_CHANNEL_SECRET)
    except Exception:
        logger.exception("Failed to initialize LINE SDK")

# Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# Static files route (if needed)
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(app.root_path, "static"), filename)

# Webhook callback
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    app.logger.info(f"Callback received length={len(body)} signature_present={'yes' if signature else 'no'}")

    if handler is None or line_bot_api is None:
        app.logger.error("LINE SDK not initialized due to missing env vars")
        # Return 200 so LINE doesn't keep retrying; adjust as needed
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
if handler is not None and MessageEvent is not None:
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

# --- Application routes (must be defined before app.run) ---
@app.route("/", methods=["GET"])
def index():
    try:
        return render_template("index.html")
    except Exception:
        app.logger.exception("Failed to render index.html")
        return make_response("kusunoki PDF Project - index not found", 200)

@app.route("/liff-entry", methods=["GET"])
def liff_entry():
    try:
        return render_template("liff-entry.html", liff_id=LIFF_ID)
    except Exception:
        app.logger.exception("Failed to render liff-entry.html")
        return make_response("LIFF entry template not found", 200)

@app.route("/api/liff/entry", methods=["POST"])
def api_liff_entry():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid_json"}), 400
    id_token = payload.get("idToken") if isinstance(payload, dict) else None
    if not id_token:
        return jsonify({"error": "missing_idToken"}), 400
    if "trial" in id_token:
        return jsonify({"action": "trial", "purchase_url": "https://kusunoki-pdf-project.onrender.com/purchase"})
    return jsonify({"action": "dashboard", "url": "/dashboard"})

# Debug route to list registered routes (remove in production)
@app.route("/_routes", methods=["GET"])
def _routes():
    rules = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
        rules.append(f"{rule} -> methods={sorted(rule.methods)}")
    return "\n".join(rules), 200, {"Content-Type": "text/plain"}

# Run server for local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.logger.info(f"Starting dev server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
