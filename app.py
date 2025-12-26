from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    ImageMessage,
    TemplateMessage,
    ButtonsTemplate,
    MessageAction,
    QuickReply,
    QuickReplyItem
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    FollowEvent
)
import os
import tempfile
from LineBot import config
from LineBot.test_backend_logic import (
    process_image, 
    process_image_mygo,
    process_image_ocr_only,
    analyze_combined_dialogue
)

app = Flask(__name__)

# 從 config.py 讀取設定 (LINE Bot SDK v3)
configuration = Configuration(access_token=config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)

# 儲存用戶狀態：{"user_id": {"mode": "analysis/sticker", "images": [path1, path2, ...]}}
user_states = {}


def get_menu_message():
    """建立功能選單的 Buttons Template 訊息"""
    return TemplateMessage(
        alt_text="請選擇功能",
        template=ButtonsTemplate(
            title="💬 聊天分析助手",
            text="請選擇你想要的功能：",
            actions=[
                MessageAction(
                    label="❤️ 感情分析",
                    text="感情分析"
                ),
                MessageAction(
                    label="😆 智慧表情包",
                    text="智慧表情包"
                )
            ]
        )
    )


def get_quick_reply():
    """建立 Quick Reply 按鈕（選擇功能）"""
    return QuickReply(
        items=[
            QuickReplyItem(
                action=MessageAction(
                    label="❤️ 感情分析",
                    text="感情分析"
                )
            ),
            QuickReplyItem(
                action=MessageAction(
                    label="😆 智慧表情包",
                    text="智慧表情包"
                )
            ),
            QuickReplyItem(
                action=MessageAction(
                    label="📋 功能選單",
                    text="選單"
                )
            )
        ]
    )


def get_upload_quick_reply(image_count):
    """建立上傳圖片時的 Quick Reply 按鈕"""
    items = [
        QuickReplyItem(
            action=MessageAction(
                label="❌ 取消",
                text="取消"
            )
        )
    ]
    
    # 有 1 張以上圖片時，顯示「開始分析」按鈕
    if image_count >= 1:
        items.insert(0, QuickReplyItem(
            action=MessageAction(
                label=f"🚀 開始分析 ({image_count}張)",
                text="開始分析"
            )
        ))
    
    return QuickReply(items=items)


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


# 處理用戶加入好友事件：顯示歡迎訊息和功能選單
@handler.add(FollowEvent)
def handle_follow(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        welcome_message = TextMessage(
            text="👋 歡迎使用聊天分析助手！\n\n我可以幫你：\n❤️ 分析聊天對話的感情狀態\n😆 根據對話推薦適合的表情包\n\n請選擇下方功能開始使用 ⬇️"
        )
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[welcome_message, get_menu_message()]
            )
        )


def cleanup_user_images(user_id):
    """清理用戶的暫存圖片"""
    if user_id in user_states and "images" in user_states[user_id]:
        for img_path in user_states[user_id]["images"]:
            if os.path.exists(img_path):
                os.remove(img_path)
    user_states.pop(user_id, None)


# 處理文字訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if text in ["感情分析", "1"]:
            # 清理之前的狀態
            cleanup_user_images(user_id)
            user_states[user_id] = {"mode": "analysis", "images": []}
            
            reply_message = TextMessage(
                text="📸 請傳送聊天截圖\n\n💡 可以傳送多張圖片，傳完後點「開始分析」按鈕",
                quick_reply=get_upload_quick_reply(0)
            )

        elif text in ["智慧表情包", "表情包", "2"]:
            # 清理之前的狀態
            cleanup_user_images(user_id)
            user_states[user_id] = {"mode": "sticker", "images": []}
            
            reply_message = TextMessage(
                text="📸 請傳送聊天截圖\n\n� 可以傳送多張圖片，傳完後點「開始分析」按鈕",
                quick_reply=get_upload_quick_reply(0)
            )

        elif text == "開始分析":
            # 開始處理所有圖片
            if user_id not in user_states or not user_states[user_id].get("images"):
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text="⚠️ 還沒有上傳圖片喔！請先選擇功能並上傳圖片"),
                            get_menu_message()
                        ]
                    )
                )
                return
            
            # 回覆處理中
            image_count = len(user_states[user_id]["images"])
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"🔄 正在分析 {image_count} 張圖片，請稍候...")]
                )
            )
            
            # 處理所有圖片
            process_all_images(user_id, line_bot_api)
            return

        elif text == "取消":
            cleanup_user_images(user_id)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="已取消 ✅"),
                        get_menu_message()
                    ]
                )
            )
            return

        elif text in ["選單", "menu", "功能", "幫助", "help"]:
            cleanup_user_images(user_id)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[get_menu_message()]
                )
            )
            return

        else:
            # 未知指令，顯示選單
            reply_message = TextMessage(
                text="你想做什麼呢？請點選下方按鈕選擇功能 �",
                quick_reply=get_quick_reply()
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[reply_message, get_menu_message()]
                )
            )
            return

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )


def process_all_images(user_id, line_bot_api):
    """處理用戶上傳的所有圖片"""
    state = user_states.get(user_id, {})
    mode = state.get("mode")
    images = state.get("images", [])
    
    try:
        if mode == "analysis":
            # 感情分析：先對所有圖片進行 OCR，合併文字後再一次傳給 AI
            all_ocr_texts = []
            for i, img_path in enumerate(images):
                print(f"📷 OCR 處理第 {i+1}/{len(images)} 張圖片: {img_path}")
                ocr_text = process_image_ocr_only(img_path)
                if ocr_text:
                    all_ocr_texts.append(f"【第{i+1}張截圖】\n{ocr_text}")
            
            if not all_ocr_texts:
                line_bot_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[
                            TextMessage(
                                text="⚠️ 無法辨識任何圖片中的文字，請確認是否為聊天截圖。",
                                quick_reply=get_quick_reply()
                            )
                        ]
                    )
                )
                return
            
            # 合併所有 OCR 文字
            combined_text = "\n\n".join(all_ocr_texts)
            print(f"📝 合併 {len(all_ocr_texts)} 張圖片的 OCR 結果，準備傳給 AI...")
            
            # 一次性傳給 AI 分析
            ai_result = analyze_combined_dialogue(combined_text)
            
            # 如果結果太長，截斷
            if len(ai_result) > 5000:
                ai_result = ai_result[:4900] + "\n\n...（內容過長已截斷）"
            
            line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[
                        TextMessage(
                            text=ai_result,
                            quick_reply=get_quick_reply()
                        )
                    ]
                )
            )

        elif mode == "sticker":
            # 智慧表情包：為每張圖片推薦表情包
            messages = []
            for i, img_path in enumerate(images):
                print(f"📷 處理第 {i+1}/{len(images)} 張圖片: {img_path}")
                image_url = process_image_mygo(img_path)
                
                if isinstance(image_url, str) and image_url.startswith("https"):
                    messages.append(
                        ImageMessage(
                            original_content_url=image_url,
                            preview_image_url=image_url
                        )
                    )
            
            if messages:
                # LINE 一次最多發送 5 則訊息
                messages = messages[:5]
                messages.append(
                    TextMessage(
                        text=f"✨ 以上是推薦給你的 {len(messages)} 個表情包！",
                        quick_reply=get_quick_reply()
                    )
                )
                line_bot_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=messages
                    )
                )
            else:
                line_bot_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[
                            TextMessage(
                                text="找不到適合的表情包 QQ\n要不要換張圖片試試？",
                                quick_reply=get_quick_reply()
                            )
                        ]
                    )
                )
    
    except Exception as e:
        print(f"❌ 處理錯誤: {e}")
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[
                    TextMessage(
                        text=f"❌ 處理過程發生錯誤：{str(e)}",
                        quick_reply=get_quick_reply()
                    )
                ]
            )
        )
    
    finally:
        # 清理所有暫存圖片
        cleanup_user_images(user_id)


# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    user_id = event.source.user_id

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessagingApiBlob(api_client)

        # 檢查用戶是否已選擇功能
        if user_id not in user_states or "mode" not in user_states[user_id]:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="請先選擇功能 😊"),
                        get_menu_message()
                    ]
                )
            )
            return

        # 下載並暫存圖片
        message_content = line_bot_blob_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
            tf.write(message_content)
            temp_file_path = tf.name
        
        # 將圖片路徑加入用戶狀態
        user_states[user_id]["images"].append(temp_file_path)
        image_count = len(user_states[user_id]["images"])
        
        # 根據圖片數量回覆不同訊息
        if image_count == 1:
            reply_text = f"✅ 收到第 1 張圖片！\n\n👆 點「開始分析」立即處理\n📸 或繼續傳送更多圖片"
        else:
            reply_text = f"✅ 已收到 {image_count} 張圖片！\n\n👆 點「開始分析」開始處理\n📸 或繼續傳送更多圖片"
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text=reply_text,
                        quick_reply=get_upload_quick_reply(image_count)
                    )
                ]
            )
        )


if __name__ == "__main__":
    app.run(port=5000)
