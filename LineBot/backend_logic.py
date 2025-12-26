import sys
import os

# 將專案根目錄加入 Python 路徑，讓前端可以引用後端模組
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 引用後端模組（不複製程式碼，後端更改時前端自動同步）
from image_recognition.structured_ocr import detect_chat_structure
from AI_response.chat_analyze import analyze_message, convert_dialogue
from mygo.test_recommend_mygo_image import recommend_mygo_image

def process_image(image_path):
    """
    處理圖片的主要邏輯：
    1. 使用 Google Vision OCR 辨識聊天截圖
    2. 轉換對話格式
    3. 使用 Gemini AI 分析對話語氣、情緒與意圖

    Args:
        image_path (str): 圖片檔案的路徑。

    Returns:
        str: AI 分析結果的文字描述。
    """
    print(f"📷 正在處理圖片: {image_path}")

    try:
        # Step 1: OCR 辨識聊天結構（左右發話者）
        print("🔍 Step 1: 執行 OCR 辨識...")
        dialogue = detect_chat_structure(image_path)
        
        if not dialogue:
            return "⚠️ 無法辨識圖片中的文字，請確認是否為聊天截圖。"
        
        # Step 2: 轉換對話格式
        print("📝 Step 2: 轉換對話格式...")
        text = convert_dialogue(dialogue)
        
        # Step 3: AI 分析對話
        print("🤖 Step 3: AI 分析對話...")
        result = analyze_message(text)
        
        return result.text  # 回傳 Gemini 的分析結果
        
    except Exception as e:
        error_msg = f"❌ 處理失敗：{str(e)}"
        print(error_msg)
        return error_msg

def process_image_mygo(image_path):
    """
    處理圖片的主要邏輯：
    1. 使用 Google Vision OCR 辨識聊天截圖
    2. 轉換對話格式
    3. 使用 Gemini AI 分析對話語氣、情緒與意圖

    Args:
        image_path (str): 圖片檔案的路徑。

    Returns:
        str: AI 分析結果的文字描述。
    """
    print(f"📷 正在處理圖片: {image_path}")

    try:
        # Step 1: OCR 辨識聊天結構（左右發話者）
        print("🔍 Step 1: 執行 OCR 辨識...")
        dialogue = detect_chat_structure(image_path)
        
        if not dialogue:
            return "⚠️ 無法辨識圖片中的文字，請確認是否為聊天截圖。"
        
        # Step 2: 轉換對話格式
        print("📝 Step 2: 轉換對話格式...")
        text = convert_dialogue(dialogue)
        
        # Step 3: AI 分析對話
        print("🤖 Step 3: AI 分析對話...")
        url = recommend_mygo_image(text)
        
        return url  # 回傳 Gemini 的分析結果
        
    except Exception as e:
        error_msg = f"❌ 處理失敗：{str(e)}"
        print(error_msg)
        return error_msg