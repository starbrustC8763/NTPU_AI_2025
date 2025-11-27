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
    prompt = f"""
    請分析以下訊息的語氣、情緒與意圖:
    訊息: "{text}"
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
    test_img = "piyan.png"  # 你可以換成你的聊天截圖
    if os.path.exists(test_img):
        print("📷 開始 OCR 辨識...")
        dialogue = detect_chat_structure(test_img)
        text = convert_dialogue(dialogue)
        print(text)
        #output = analyze_message(text)
        #print(output)
main()