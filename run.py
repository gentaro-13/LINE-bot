# run.py  ── Cloud Run 用 FastAPI + LINE SDK（同期版）
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = FastAPI()

# ---- LINE SDK（同期） ----
line_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler  = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# ---- Dify 用 HTTP クライアント（同期） ----
http_client = httpx.Client()

# ──────────────── ルート定義 ────────────────
@app.get("/callback")
def callback_health() -> PlainTextResponse:         # ブラウザ確認用
    return PlainTextResponse("OK", status_code=200)

@app.post("/callback")
async def callback(request: Request):
    body = await request.body()
    sig  = request.headers.get("X-Line-Signature", "")
    try:
        handler.handle(body.decode(), sig)          # ★同期呼び出し
    except InvalidSignatureError:                   # 検証イベントなどは握りつぶす
        return "ok"
    return "ok"

# ---- LINE からのメッセージイベント ----
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    user_id = event.source.user_id
    text    = event.message.text

    # === Dify Chatflow 呼び出し（同期） ===
    resp = http_client.post(
        f"{os.getenv('DIFY_BASE')}/v1/chat-messages",
        headers={"Authorization": f"Bearer {os.getenv('DIFY_KEY')}"},
        json={
            "inputs": {"text": text},
            "query":  text,
            "user":   user_id
        }
    )
    answer = resp.json().get("answer", "すみません、うまく答えられませんでした。")

    # === LINE へ返信（同期） ===
    line_api.reply_message(
        event.reply_token,
        TextSendMessage(text=answer)
    )
