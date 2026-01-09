# survey_reply_handler.py
# 使い方:
# 1) このファイルを既存Webhookプロジェクトに置く
# 2) 環境変数 LINE_CHANNEL_ACCESS_TOKEN を設定するか、下の変数に直接代入する
# 3) 既存の /survey_callback エンドポイントから handle_survey_request(payload) を呼ぶ

import os
import json
import pandas as pd
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定 ---
# 環境変数に設定することを推奨
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
CSV_PATH = os.path.join(os.getcwd(), "companies_master_final.csv")  # 必ず最新のCSVを置く
# --- /設定ここまで ---

line_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def _safe_int(v, default=0):
    try:
        return int(float(v))
    except Exception:
        return default

def select_top3_from_csv(csv_path, survey_payload=None):
    """
    companies_master_final.csv を読み、合成スコアで上位3社を返す
    戻り値: list of dict {company_name, industry, overview, medical_relevance_score, hybrid_fit_score}
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} が見つかりません")

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    # 数値化
    df["medical_relevance_score"] = pd.to_numeric(df.get("medical_relevance_score", 0), errors="coerce").fillna(0)
    df["hybrid_fit_score"] = pd.to_numeric(df.get("hybrid_fit_score", 0), errors="coerce").fillna(0)
    df["risk_level"] = pd.to_numeric(df.get("risk_level", 0), errors="coerce").fillna(100)

    # 合成スコア（既存提案ロジック）
    df["composite"] = df["medical_relevance_score"] * 2 + df["hybrid_fit_score"] - df["risk_level"]
    df_sorted = df.sort_values(by="composite", ascending=False)

    top3 = []
    for _, row in df_sorted.head(3).iterrows():
        top3.append({
            "company_name": row.get("company_name", "").strip(),
            "industry": row.get("industry", "").strip(),
            "overview": (row.get("short_description", "") or row.get("company_overview", "")).strip(),
            "medical_relevance_score": int(row.get("medical_relevance_score") or 0),
            "hybrid_fit_score": int(row.get("hybrid_fit_score") or 0)
        })
    return top3

def format_reply_text(top3):
    """
    要件に合わせて「企業概要」と「提案理由」のみを含むテキストを作成し、
    最後に締めの文言を付ける
    """
    lines = ["以下は、アンケート結果に基づく「ある程度マッチしている企業」の例です。参考にしてください。\n"]
    for i, c in enumerate(top3, start=1):
        lines.append(f"{i}) {c['company_name']}")
        lines.append(f"企業概要: {c['overview']}")
        lines.append(f"提案理由: 医療関連性 {c['medical_relevance_score']}、ハイブリッド適合 {c['hybrid_fit_score']}。\n")
    lines.append("これはほんの世間のごく一部です。今後を決めるのはあなた次第")
    return "\n".join(lines)

def handle_survey_request(payload_json):
    """
    既存Webhookのアンケート受信ハンドラから呼ぶ関数
    入力: payload_json (dict) 例:
      {
        "user_id": "Uxxxxxxxxxxxx",   # 任意。LINE userId を渡せば push 送信する
        "answers": { ... }            # 任意。今回は未使用
      }
    戻り値:
      - user_id が LINE userId の場合: {"status":"sent_via_line_push"} または {"status":"failed","error":...}
      - user_id が無い／LINE IDでない場合: {"reply_text": "..."} を返すのでアンケート側で表示する
    """
    # CSV から上位3社を選定
    try:
        top3 = select_top3_from_csv(CSV_PATH, survey_payload=payload_json.get("answers") if payload_json else None)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    reply_text = format_reply_text(top3)

    user_id = payload_json.get("user_id") if isinstance(payload_json, dict) else None
    if user_id and str(user_id).startswith("U"):
        # LINE userId が渡されている場合は push で送信
        try:
            # LINE のメッセージ長制限に注意。長ければ分割して送る
            line_api.push_message(user_id, TextSendMessage(text=reply_text))
            return {"status": "sent_via_line_push"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    else:
        # LINE ID が無い場合は reply_text を返す
        return {"reply_text": reply_text}
