
import os
import sys
import logging
from flask import Flask, request, jsonify

# 繝励Ο繧ｸ繧ｧ繧ｯ繝医Ν繝ｼ繝医ｒ sys.path 縺ｫ霑ｽ蜉
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from line_tools.survey_reply_handler import handle_survey_request, send_push_message_if_needed

# LINE SDK
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# 迺ｰ蠅・､画焚・・ender 縺ｮ Environment 縺ｫ險ｭ螳夲ｼ・
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
SURVEY_CALLBACK_TOKEN = os.environ.get("SURVEY_CALLBACK_TOKEN")  # 莉ｻ諢・

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

# 譛ｬ逡ｪ逕ｨ /callback・育ｽｲ蜷肴､懆ｨｼ縺ゅｊ・・
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
                # 蠢・ｦ√↑繧峨％縺薙〒蜊ｳ譎ょｿ懃ｭ斐ｄ DB 逋ｻ骭ｲ縺ｪ縺ｩ繧定｡後≧
        except Exception:
            app.logger.exception("Error handling event")

    return "OK", 200

# /survey_callback : 繧｢繝ｳ繧ｱ繝ｼ繝育ｵ先棡繧貞女縺大叙繧雁・逅・☆繧・
@app.route("/survey_callback", methods=["POST"])
def survey_callback():
    # 莉ｻ諢上ヨ繝ｼ繧ｯ繝ｳ縺瑚ｨｭ螳壹＆繧後※縺・ｋ蝣ｴ蜷医・繝√ぉ繝・け・域悽逡ｪ謗ｨ螂ｨ・・
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

    # push 繧定ｩｦ縺ｿ繧具ｼ・INE 險ｭ螳壹′縺ゅｌ縺ｰ・・
    try:
        send_push_message_if_needed(line_bot_api, result)
    except Exception:
        app.logger.exception("Error sending push message (non-fatal)")

    return jsonify(result), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

