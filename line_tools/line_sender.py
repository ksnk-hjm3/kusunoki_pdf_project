from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
    URIAction,
    MessageAction,
    CarouselColumn,
    CarouselTemplate,
    TemplateMessage
)

# =========================================================
# Kai が貼る必要があるのはここだけ
# =========================================================
CHANNEL_ACCESS_TOKEN = "JyteEO/ShmBaNHkrIpNQEGJRNcd5YqrKZUotk3RlAPOVQiFcIVKS4Fgqgb5uoWBwsZyyNOGdJwt7VbiVEXKW0M5ocqS2o1JgctRehZUTyOKpkj/f074yUaQn04FEnG+qRSrfWaUJdlTa6mJ1MSYhfQdB04t89/1O/w1cDnyilFU=
"


# =========================================================
# LINE API 初期化
# =========================================================
config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)


# =========================================================
# テキスト送信
# =========================================================
def send_text(user_id, text):
    with ApiClient(config) as api_client:
        messaging_api = MessagingApi(api_client)

        body = PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=text)]
        )
        messaging_api.push_message(body)


# =========================================================
# カルーセル送信（上位3社）
# =========================================================
def send_carousel(user_id, companies):
    columns = []

    for c in companies[:3]:  # 上位3社
        title = f"{c['name'][:20]}"  # 長すぎるとエラーになるので20文字制限

        text_lines = []
        text_lines.append(f"医療スコア：{c.get('medical_score', 0)}")

        if c.get("tags"):
            text_lines.append(" / ".join(c["tags"][:2]))

        if c.get("recruit_url"):
            text_lines.append("採用ページあり")
        else:
            text_lines.append("採用ページなし")

        text = "\n".join(text_lines)

        actions = [
            MessageAction(
                label="詳細を見る",
                text=f"{c['name']} の詳細を知りたい"
            ),
            URIAction(
                label="公式サイト",
                uri=c.get("official_url", "https://google.com")
            )
        ]

        if c.get("recruit_url"):
            actions.append(
                URIAction(
                    label="採用ページ",
                    uri=c["recruit_url"]
                )
            )

        columns.append(
            CarouselColumn(
                title=title,
                text=text,
                actions=actions
            )
        )

    carousel = CarouselTemplate(columns=columns)
    message = TemplateMessage(alt_text="企業推薦", template=carousel)

    with ApiClient(config) as api_client:
        messaging_api = MessagingApi(api_client)
        body = PushMessageRequest(
            to=user_id,
            messages=[message]
        )
        messaging_api.push_message(body)
