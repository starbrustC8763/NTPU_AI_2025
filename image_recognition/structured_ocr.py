import io
import json
from google.cloud import vision
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
def detect_chat_structure(image_path: str, threshold_ratio: float = 0.5) -> List[Dict]:
    """
    使用 Google Vision Document OCR 偵測聊天內容，並根據文字位置判斷左右發話者。

    Args:
        image_path (str): 圖片路徑
        threshold_ratio (float): 分界比例（0.5 表示圖片中線）
    Returns:
        List[Dict]: 包含發話者與文字的結構化列表
    """
    client = vision.ImageAnnotatorClient()

    # 讀取圖片
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    # 使用 document_text_detection 取得完整版面資訊
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")

    results = []
    width = None

    # 遍歷每一頁（通常是單張）
    for page in response.full_text_annotation.pages:
        width = page.width or 1000
        for block in page.blocks:
            # 組合 block 文字
            block_text = ""
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    block_text += word_text
                block_text += " "

            # 判斷氣泡在左或右
            x_positions = [v.x for v in block.bounding_box.vertices]
            avg_x = sum(x_positions) / len(x_positions)
            #side = "left" if avg_x < width * threshold_ratio else "right"
            
            if avg_x < width * 0.6 and avg_x > width * 0.4:
                side = "middle"
            elif avg_x < width * threshold_ratio:
                side = "left"
            else:
                side = "right"
            # 取平均 Y 位置（用於排序）
            avg_y = sum([v.y for v in block.bounding_box.vertices]) / len(block.bounding_box.vertices)

            results.append({
                "speaker": side,
                "text": block_text.strip(),
                "y_pos": avg_y
            })

    # 依照垂直位置排序
    results.sort(key=lambda r: r["y_pos"])

    # 移除空文字、只保留必要欄位
    structured_dialogue = [
        {"speaker": r["speaker"], "text": r["text"]}
        for r in results if r["text"]
    ]

    return structured_dialogue

def main():
    # 測試範例
    test_img = "piyan.png"  # 你可以換成你的聊天截圖
    if os.path.exists(test_img):
        print("📷 開始 OCR 辨識...")
        dialogues = detect_chat_structure(test_img)
        print("\n======================")
        print("📜 結構化辨識結果：")
        print("======================")
        print(json.dumps(dialogues, ensure_ascii=False, indent=2))
    else:
        print(f"⚠️ 找不到測試圖片:{test_img}")
main()