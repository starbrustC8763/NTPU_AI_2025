import google.generativeai as genai
import os
from dotenv import load_dotenv
from image_recognition.structured_ocr import detect_chat_structure

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("環境變數 GEMINI_API_KEY 尚未設定")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_message(text):
    prompt = f"""你是一位專業的對話分析師與伴侶諮商師。
    請按照以下格式回覆（去除所有Markdown語法）：
    一、語氣 (Tone)
    - 列出對話中觀察到的語氣特點
    - 例如：
        - 用詞
        - 語調

    二、情緒 (Emotion)  
    - 分析雙方的情緒狀態
    - 例如：
        - 用詞
        - 語調
        - 感情色彩

    三、意圖 (Intention)
    - 分析雙方各自的目的

    總結
    - 用一段話總結整體對話特性，以及雙方的感情狀況
    ======
    請分析以下聊天記錄：
    {text}
    """
    message = model.generate_content(prompt)
    return message.text
def convert_dialogue(json_list):
    """
    將格式:
    {
        "speaker": "right",
        "text": "要不要出去逛逛?"
    }
    轉成:
    (我)要不要出去逛逛?

    speaker = "right" → (我)
    speaker = "left" → (對方)
    speaker = "middle" → (時間戳or系統訊息)
    """

    result_lines = []
    for item in json_list:
        spk = item.get("speaker")
        text = item.get("text", "")

        if spk == "right":
            prefix = "(我)"
        elif spk == "left":
            prefix = "(對方)"
        elif spk == "middle":
            prefix = "(時間戳or系統訊息)"
        else:
            prefix = "(未知)"

        result_lines.append(f"{prefix}{text}")

    return "\n".join(result_lines)


def main():
    test_img = "chat.webp"  # 你可以換成你的聊天截圖
    if os.path.exists(test_img):
        print("📷 開始 OCR 辨識...")
        dialogue = detect_chat_structure(test_img)
        text = convert_dialogue(dialogue)
        #print(text)
        output = analyze_message(text)
        print(output)
#main()