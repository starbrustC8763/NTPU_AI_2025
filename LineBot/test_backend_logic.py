import sys
import os

# 將專案根目錄加入 Python 路徑，讓前端可以引用後端模組
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 引用後端模組（不複製程式碼，後端更改時前端自動同步）
from image_recognition.structured_ocr import detect_chat_structure
from AI_response.chat_analyze import analyze_message, convert_dialogue
from mygo.test_recommend_mygo_image import recommend_mygo_image


def process_image_ocr_only(image_path):
    """
    只執行 OCR 辨識，回傳對話文字。
    用於多張圖片時，先分別 OCR，再合併文字一次傳給 AI。

    Args:
        image_path (str): 圖片檔案的路徑。

    Returns:
        str: 轉換後的對話文字，若辨識失敗則回傳 None。
    """
    print(f"📷 正在 OCR 處理圖片: {image_path}")

    try:
        # Step 1: OCR 辨識聊天結構（左右發話者）
        print("🔍 執行 OCR 辨識...")
        dialogue = detect_chat_structure(image_path)
        
        if not dialogue:
            return None
        
        # Step 2: 轉換對話格式
        print("📝 轉換對話格式...")
        text = convert_dialogue(dialogue)
        
        return text
        
    except Exception as e:
        error_msg = f"❌ OCR 處理失敗：{str(e)}"
        print(error_msg)
        return None


def analyze_combined_dialogue(combined_text):
    """
    將合併的對話文字傳給 AI 進行分析。

    Args:
        combined_text (str): 合併後的完整對話文字。

    Returns:
        str: AI 分析結果的文字描述。
    """
    print("🤖 AI 分析合併後的對話...")
    
    try:
        result = analyze_message(combined_text)
        return result.text
        
    except Exception as e:
        error_msg = f"❌ AI 分析失敗：{str(e)}"
        print(error_msg)
        return error_msg


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