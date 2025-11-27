import os
import re
import cv2
import pytesseract
from google.cloud import vision
import io
import numpy as np

# 指定 Tesseract 執行路徑（如有需要）
#pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# 初始化 Google Vision 客戶端（若環境變數已設定會自動讀取）
try:
    vision_client = vision.ImageAnnotatorClient()
except Exception as e:
    vision_client = None
    print(f"⚠️ 無法初始化 Google Vision Client：{e}")


# ========= 圖像前處理 =========
def preprocess_image(image_path: str, save_debug=False) -> np.ndarray:
    print(f"🧩 正在處理圖片：{image_path}")
    image = cv2.imread(image_path)

    # 轉灰階
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 去噪
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    # 二值化
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if save_debug:
        debug_path = os.path.splitext(image_path)[0] + "_preprocessed.png"
        cv2.imwrite(debug_path, thresh)
        print(f"🖼️ 已儲存處理後圖片：{debug_path}")

    return thresh


# ========= Tesseract 辨識 =========
def extract_text_tesseract(image: np.ndarray) -> str:
    config = "--psm 6"
    text = pytesseract.image_to_string(image, lang="chi_tra+eng", config=config)
    return text.strip()


# ========= Google Vision 辨識 =========
def extract_text_google(image_path: str) -> str:
    if not vision_client:
        print("⚠️ 未初始化 Vision Client，跳過 Google Vision 辨識。")
        return ""

    with io.open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = vision_client.text_detection(image=image)
    if response.error.message:
        print(f"⚠️ Vision API 回傳錯誤：{response.error.message}")
        return ""

    texts = response.text_annotations
    if not texts:
        return ""

    full_text = texts[0].description
    return full_text.strip()


# ========= 智能判斷是否亂碼 =========
def is_garbled(text: str) -> bool:
    if not text or len(text.strip()) < 6:
        return True
    # 檢查是否多為非文字符號
    symbol_ratio = len(re.findall(r"[^\w\u4e00-\u9fff]", text)) / len(text)
    return symbol_ratio > 0.6


# ========= 主流程：雙引擎辨識 =========
def recognize_text(image_path: str, save_debug=True, merge=False) -> str:
    preprocessed_img = preprocess_image(image_path, save_debug=save_debug)

    print("\n🔠 使用 Tesseract 辨識中...")
    text_tesseract = extract_text_tesseract(preprocessed_img)
    print(f"🧾 Tesseract 結果：{text_tesseract[:100]}{'...' if len(text_tesseract) > 100 else ''}")

    print("\n☁️ 使用 Google Vision API 辨識中...")
    text_google = extract_text_google(image_path)
    print(f"🧾 Google Vision 結果：{text_google[:100]}{'...' if len(text_google) > 100 else ''}")

    # ========== 比較結果 ==========
    len_t, len_g = len(text_tesseract), len(text_google)
    print(f"\n📊 結果比較：Tesseract 長度={len_t}, Google 長度={len_g}")

    # ========== 輸出策略 ==========
    if merge:
        merged = text_tesseract.strip() + "\n" + ("-" * 40) + "\n" + text_google.strip()
        print("\n✅ 輸出合併結果。")
        return merged
    else:
        print("\n✅ 輸出 Google Vision 結果（建議精準度最高）。")
        return text_google.strip() if text_google else text_tesseract.strip()

if __name__ == "__main__":
    # 測試範例
    test_img = "piyan.png"  # 你可以換成你的聊天截圖
    if os.path.exists(test_img):
        print("📷 開始 OCR 辨識...")
        lines = recognize_text(test_img)
        print("\n辨識結果：")
    else:
        print(f"⚠️ 找不到測試圖片:{test_img}")