# run.py  ★丸ごと貼り換えてOK
import os, httpx
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = FastAPI()

# --- LINE SDK (同期版) ---
line_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler   = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# --- HTTP クライアント (Dify 用に async で使う) ---
http_client = httpx.AsyncClient()

@app.post("/callback")
async def webhook(request: Request):
    body = await request.body()
    sig  = request.headers.get("X-Line-Signature", "")
    try:
        handler.handle(body.decode(), sig)   # 同期呼び出し
    except InvalidSignatureError:
        # LINE の検証要求などはダミー署名なので握りつぶす
        return "ok"
    return "ok"

@app.get("/callback")           # ★接続確認(GET)用
def callback_health():
    return "ok"

@handler.add(MessageEvent, message=TextMessage)
async def handle_message(event):
    user_id = event.source.user_id
    text    = event.message.text

    # --- Dify Chatflow を呼び出す（非同期）---
    resp = await http_client.post(
        f"{os.getenv('DIFY_BASE')}/v1/chat-messages",
        headers={"Authorization": f"Bearer {os.getenv('DIFY_KEY')}"},
        json={
            "inputs": {"text": text},
            "query": text,
            "user":  user_id
        }
    )
    answer = resp.json().get("answer", "すみません、うまく答えられませんでした。")

    # --- LINE に同期で返信 ---
    line_api.reply_message(
        event.reply_token,
        TextSendMessage(text=answer)
    )
