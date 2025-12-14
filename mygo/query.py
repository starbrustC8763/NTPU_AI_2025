import google.generativeai as genai
import faiss
import numpy as np
import json

genai.configure(api_key="你的_Gemini_API_KEY")

# 載入資料
with open("mygo_labeled.json", "r", encoding="utf8") as f:
    data = json.load(f)

index = faiss.read_index("mygo.index")
MODEL = "gemini-1.5-flash"
EMB_MODEL = "text-embedding-004"


def detect_tone(text):
    prompt = f"""
請判斷下面句子的語氣從以下標籤多選：
{", ".join(TAGS)}

句子：{text}

請只輸出 JSON array，例如：
["好奇","輕鬆"]
"""
    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    return json.loads(resp.text)


def embed(text):
    return np.array(
        genai.embed_content(model=EMB_MODEL, content=text)["embedding"],
        dtype="float32"
    )


def find_matching_image(query_text, top_k=20):
    # Step1: 語氣分類
    tones = detect_tone(query_text)

    # Step2: embedding 查詢
    q_emb = embed(query_text).reshape(1, -1)
    distances, indices = index.search(q_emb, top_k)

    # Step3: 過濾語氣相符的句子
    candidates = []
    for idx in indices[0]:
        item = data[idx]
        if any(t in item["tones"] for t in tones):
            candidates.append(item)

    if not candidates:
        # 如果沒有語氣匹配 → 回傳最接近的句子
        candidates = [data[indices[0][0]]]

    best = candidates[0]

    # Step4: 拼出圖片網址
    url = f"https://mypic.0m0.uk/images/{best['season']}/{best['episode']}/{best['frame_prefer']}.webp"

    return {
        "input_tones": tones,
        "text": best["text"],
        "tones": best["tones"],
        "season": best["season"],
        "episode": best["episode"],
        "frame": best["frame_prefer"],
        "image_url": url
    }


# 測試
print(find_matching_image("真的好可愛喔，我受不了了"))
