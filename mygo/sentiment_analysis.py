import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
# 初始化 Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

TAGS = [
    "開心","興奮","好奇","困惑","傷心","難過","生氣","不耐煩","緊張","害羞","臉紅",
    "失望","無奈","中性","傲嬌","可憐","冷淡","撒嬌","敷衍","正式","輕鬆","幽默","諷刺",
    "自嘲","崩潰","曖昧","強勢","弱勢","詢問","拒絕","關心","試探","抱怨","暗示","回避"
]

def analyze_tone(text: str) -> dict:
    tag_list = "、".join(TAGS)

    prompt = f"""
你是一個「聊天語氣分類器」，不是自由生成模型。

請從【指定標籤清單】中，選出最符合該句話的：
- 1 個「主要情緒 emotion」
- 1 個「主要語氣 tone」
- 1 個「主要意圖 intent」

【指定標籤清單】
{tag_list}

⚠️ 規則：
1. emotion、tone、intent 的值「只能」從上述標籤中選
2. 如果完全不符合，請填寫空字串 ""
3. 不得自行發明新詞
4. 僅輸出 JSON，不要任何說明文字

訊息內容：
{text}

JSON 格式：
{{
  "emotion": "",
  "tone": "",
  "intent": "",
  "confidence": 0.0
}}
"""

    response = model.generate_content(prompt)
    return response.text
