import os
from google.cloud import vision
import google.auth.exceptions
import io

def verify_google_vision_key(image_path=None):
    print("🔍 開始檢查 Google Vision API 設定...\n")

    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        print("❌ 未設定環境變數：GOOGLE_APPLICATION_CREDENTIALS")
        print("請執行以下指令（替換路徑為你的 JSON 憑證）：")
        print('export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"\n')
        return

    if not os.path.exists(key_path):
        print(f"❌ 找不到憑證檔案：{key_path}")
        return

    print(f"✅ 憑證檔案存在：{key_path}\n")

    try:
        client = vision.ImageAnnotatorClient()
        print("✅ 成功初始化 Vision Client。")

        if image_path and os.path.exists(image_path):
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)

            if response.error.message:
                print(f"⚠️ API 回傳錯誤：{response.error.message}")
            else:
                print("✅ 成功辨識圖片內容：\n")
                print(response.text_annotations[0].description if response.text_annotations else "（未偵測到文字）")
        else:
            print("⚠️ 未指定圖片路徑，因此未進行實際辨識。")
            print("💡 用法：python verify_vision_key.py <圖片路徑>")
    except google.auth.exceptions.DefaultCredentialsError:
        print("❌ 無法使用憑證登入，請確認 JSON 檔內容正確。")
    except Exception as e:
        print(f"❌ 發生例外錯誤：{e}")

if __name__ == "__main__":
    image_path = "example_chat.jpg"
    verify_google_vision_key(image_path)
