# line_tools/line_server.py
import sys
import traceback
import os
import logging

# 即時出力とログ設定
print("=== STARTUP: BEGIN ===", flush=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 捕捉不能な例外を必ず出力するためのガード
try:
    print("Attempting imports...", flush=True)
    from flask import Flask, request, jsonify
    print("Flask imported OK", flush=True)
except Exception:
    print("IMPORT ERROR", flush=True)
    traceback.print_exc(file=sys.stdout)
    # ここで終了して Render のログに出るはず
    sys.exit(1)

# さらにアプリ初期化全体を try で囲む
try:
    app = Flask(__name__)
    print("Flask app created", flush=True)

    # 環境変数チェック
    PORT = int(os.environ.get("PORT", 5000))
    print(f"PORT from env: {PORT}", flush=True)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/callback", methods=["POST"])
    def callback():
        body = request.get_data(as_text=True)
        logger.info("Callback received length=%d", len(body))
        return "OK", 200

except Exception:
    print("APP INIT ERROR", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)

# 実行時の例外も確実にログに出す
def run_dev():
    try:
        print(f"Starting dev server on 0.0.0.0:{PORT}", flush=True)
        app.run(host="0.0.0.0", port=PORT)
    except Exception:
        print("RUNTIME ERROR", flush=True)
        traceback.print_exc(file=sys.stdout)
        # 例外が出たら終了コードを返す
        sys.exit(1)

if __name__ == "__main__":
    run_dev()
