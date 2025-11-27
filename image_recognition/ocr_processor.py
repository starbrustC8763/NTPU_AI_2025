# image_recognition/ocr_processor.py
"""
OCR 模組 - 用於將聊天截圖轉成文字資料
支援中英混合辨識，包含基本前處理與錯誤處理
"""

import pytesseract
from PIL import Image, ImageOps, ImageFilter
import cv2
import numpy as np
import os


def preprocess_image(image_path: str, save_debug: bool = True) -> np.ndarray:
    """
    讀取圖片並進行前處理，提升 OCR 準確率。
    若 save_debug=True，會將每個步驟的圖片儲存在 ./debug_images/ 方便除錯。
    """
    import os

    # === 建立 debug 圖片資料夾 ===
    debug_dir = "debug_images"
    if save_debug and not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    # === 1. 讀取圖片 ===
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"找不到圖片檔案：{image_path}")

    if save_debug:
        cv2.imwrite(os.path.join(debug_dir, "1_original.jpg"), img)

    # === 2. 灰階化 ===
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if save_debug:
        cv2.imwrite(os.path.join(debug_dir, "2_gray.jpg"), gray)

    # === 3. 去雜訊 ===
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    if save_debug:
        cv2.imwrite(os.path.join(debug_dir, "3_blur.jpg"), blur)

    # === 4. 自適應閾值二值化 ===
    binary = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )
    if save_debug:
        cv2.imwrite(os.path.join(debug_dir, "4_binary.jpg"), binary)

    # === 5. 去除小雜點（開運算） ===
    kernel = np.ones((1, 1), np.uint8)
    clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    if save_debug:
        cv2.imwrite(os.path.join(debug_dir, "5_clean.jpg"), clean)

    # === 6. 可選：自動反轉亮度（白底黑字轉黑底白字） ===
    white_ratio = np.mean(clean > 127)
    if white_ratio > 0.5:  # 若背景太亮，反轉顏色
        clean = cv2.bitwise_not(clean)
        if save_debug:
            cv2.imwrite(os.path.join(debug_dir, "6_inverted.jpg"), clean)

    return img


def extract_text(image_path: str, lang: str = "chi_tra+eng") -> str:
    """
    使用 Tesseract OCR 進行圖片文字辨識。
    預設語言為中英文混合。
    """
    try:
        preprocessed = preprocess_image(image_path, save_debug=True)
        config = '--psm 6 --oem 3'
        print("[INFO] 開始 OCR 辨識...")
        text = pytesseract.image_to_string(preprocessed, lang=lang, config=config)
        print("[DEBUG OCR Raw Output]:", repr(text))
        cleaned = " ".join(text.split())
        return cleaned

    except Exception as e:
        print(f"[ERROR] OCR 辨識失敗：{e}")
        return ""


def extract_chat_lines(image_path: str) -> list:
    """
    將 OCR 文字切割成一行一行的對話形式
    （方便後續對話分析模組處理）
    """
    text = extract_text(image_path)
    if not text:
        return []

    # 按句號、問號、換行符拆解
    lines = [
        line.strip()
        for line in text.replace("。", "\n").replace("?", "?\n").split("\n")
        if len(line.strip()) > 0
    ]
    return lines


if __name__ == "__main__":
    # 測試範例
    test_img = "example_chat.jpg"  # 你可以換成你的聊天截圖
    if os.path.exists(test_img):
        print("📷 開始 OCR 辨識...")
        lines = extract_chat_lines(test_img)
        print("\n辨識結果：")
        for i, line in enumerate(lines, 1):
            print(f"{i}. {line}")
    else:
        print("⚠️ 找不到測試圖片 example_chat.png")
