from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, ImageMessage, TextMessage, TextSendMessage
)
import os
import tempfile
from LineBot import config
from LineBot.backend_logic import process_image,process_image_mygo
from linebot.models import ImageSendMessage

app = Flask(__name__)

# 從 config.py 讀取設定
line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)

user_states = {}
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# 處理文字訊息：提示用戶傳送圖片
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text in ["感情分析", "1"]:
        user_states[user_id] = "analysis"
        reply = "好，請傳送你們的聊天截圖 📸"

    elif text in ["智慧表情包", "表情包", "2"]:
        user_states[user_id] = "sticker"
        reply = "好，請傳送聊天截圖，我幫你選表情包 😆"

    else:
        reply = (
            "你想做什麼呢？\n"
            "1️⃣ 感情分析\n"
            "2️⃣ 智慧表情包回覆\n\n"
            "請回覆 1 或 2"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    mode = user_states.get(user_id)

    if not mode:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請先選擇功能：感情分析 或 智慧表情包 😊")
        )
        return

    # 先回覆處理中
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="處理中，請稍候...")
    )

    # 下載圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        temp_file_path = tf.name

    try:
        if mode == "analysis":
            result_text = process_image(temp_file_path)

            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=result_text)
            )

        elif mode == "sticker":
            image_url = process_image_mygo(temp_file_path)

        if isinstance(image_url, str) and image_url.startswith("https"):
            line_bot_api.push_message(
                user_id,
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            )
        else:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text="找不到適合的表情包 QQ")
            )

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


if __name__ == "__main__":
    app.run(port=5000)

