import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
import re
load_dotenv()
# 初始化 Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

TAGS = [
    "開心","興奮","好奇","困惑","傷心","難過","生氣","不耐煩","緊張","害羞","臉紅",
    "失望","無奈","中性","傲嬌","可憐","冷淡","撒嬌","敷衍","正式","輕鬆","幽默","諷刺",
    "自嘲","崩潰","曖昧","強勢","弱勢","詢問","拒絕","關心","試探","抱怨","暗示","回避"
]

# === 設定 ===
json_path = "mygo/mygo_labeled.json"  # 你的 JSON 檔案
base_url = "https://mypic.0m0.uk/images"  # 圖片資料庫主網址
download_dir = "mygo_images"  # 如果要下載圖片，存在這裡

# 讀 mapping JSON
with open("mygo/mapping_mygo.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

# === 讀取 JSON ===
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def safe_json_loads(text: str) -> dict:
    if not text:
        raise ValueError("Empty response")

    # 移除 ```json ``` 或 ```
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()

    return json.loads(text)

def analyze_tone(text: str) -> dict:
    tag_list = "、".join(TAGS)

    prompt = f"""
你是一個「聊天語氣分類器」，不是自由生成模型。

請從【指定標籤清單】中，選出最符合該句話的：
- 3個情緒 emotion
- 3個語氣 tone
- 3個意圖 intent

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

    try:
        response = model.generate_content(prompt)
        print("RAW:", repr(response.text))
        return safe_json_loads(response.text)

    except Exception as e:
        print(f"⚠️ Gemini 呼叫失敗：{e}")
        return {
            "emotion": "",
            "tone": "",
            "intent": "",
            "confidence": 0.0
        }
# === 查詢函式 ===
def find_image_by_text(text, download=False):
    results = [item for item in data if item.get("text") == text]

    if not results:
        print(f"❌ 找不到文字：{text}")
        return None

    for item in results:
        season = item.get("season")
        episode = item.get("episode")
        frame_prefer = item.get("frame_prefer")

        if None in (season, episode, frame_prefer):
            print(f"⚠️ 欄位不完整：{item}")
            continue

        image_url = f"{base_url}/{season}/{episode}/{frame_prefer}.webp"
        print(f"✅ {text} → {image_url}")

        # 如果要下載圖片
        if download:
            os.makedirs(download_dir, exist_ok=True)
            filename = f"{download_dir}/{text}.webp"

            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"💾 已下載：{filename}")
                else:
                    print(f"⚠️ 無法下載圖片 ({response.status_code})：{image_url}")
            except Exception as e:
                print(f"⚠️ 下載失敗：{e}")

        return image_url  # 回傳第一筆找到的結果

def build_candidates(mygo_data, user_text: str):
    """
    1. 先分析使用者語氣
    2. 只挑 tone 有對應的 MyGO text
    """

    tone_result = analyze_tone(user_text)
    user_tone = tone_result.get("tone", "")

    if not user_tone:
        # 如果分析不出 tone，就全部回傳（保底）
        return [
            {"text": item["text"], "tones": item.get("tones", [])}
            for item in mygo_data
        ]

    candidates = []

    for item in mygo_data:
        item_tones = item.get("tones", [])
        if user_tone in item_tones:
            candidates.append({
                "text": item["text"],
                "tones": item_tones
            })

    # 如果完全沒配對到，也要有 fallback
    if not candidates:
        candidates = [
            {"text": item["text"], "tones": item.get("tones", [])}
            for item in mygo_data
        ]

    return candidates



def select_mygo_reply(user_text, candidates):
    candidate_block = "\n".join(
        f"{i+1}. {c['text']}{','.join(c['tones'])}"
        for i, c in enumerate(candidates)
    )

    prompt = f"""
你是一個聊天回覆選擇器。

使用者訊息：
{user_text}

以下是 50 個「固定候選回覆」，每個都有語氣標籤。
請選出「最適合回覆使用者的那一句」。

候選回覆：
{candidate_block}

規則：
1. 只能選一個
2. 不得改寫文字
3. 只輸出 JSON
4. 如果沒有任何適合的，請回傳空字串 ""

輸出格式：
{{
  "selected_text": ""
}}
"""

    response = model.generate_content(prompt)
    data = safe_json_loads(response.text)
    return data.get("selected_text", "")

def recommend_mygo_image(user_text,download=False):
    candidates = build_candidates(data, user_text)

    selected_text = select_mygo_reply(user_text, candidates)

    if not selected_text:
        return None
    images = find_image_by_text(selected_text, download)

    if not images:
        return None

    return images


def main():
    text="哈哈笑死可憐"
    recommend_mygo_image(text,download=True)
#main()