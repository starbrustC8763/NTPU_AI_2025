import google.generativeai as genai
import json
import re
import time
import csv
import os
from tqdm import tqdm
from datetime import datetime

# ========== 設定 ==========
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
MODEL = "gemini-2.5-flash"

INPUT_FILE = "mygo/mygo_new_data.json"
OUTPUT_FILE = "mygo/mygo_labeled.json"
CHECKPOINT_FILE = "checkpoint.json"
LOG_FILE = "log.csv"

SAVE_INTERVAL = 25   # 每 25 筆寫一次 checkpoint

# ========== 語氣標籤 ==========
TAGS = [
    "開心","興奮","好奇","困惑","傷心","難過","生氣","不耐煩","緊張","害羞","臉紅",
    "失望","無奈","中性","傲嬌","可憐","冷淡","撒嬌","敷衍","正式","輕鬆","幽默","諷刺",
    "自嘲","崩潰","曖昧","強勢","弱勢","詢問","拒絕","關心","試探","抱怨","暗示","回避"
]

# ========== 屏蔽規則（可新增）==========
blocked_rules = [
    (r"^\s*$", "空白"),
    (r"www\.|http", "網址"),
    (r"^\d+$", "純數字"),
    (r"[Ff][Uu][Cc][Kk]", "髒話"),
    (r"小祥", "小祥"),   # 你要求加入的例子
    (r"立希", "立希"), 
    (r"祥子", "祥子"), 
    (r"愛音", "愛音"), 

    # 再加其他你想擋的詞
]


# ========== is_blocked：回傳原因 ==========
def is_blocked(text: str):
    for pattern, reason in blocked_rules:
        if re.search(pattern, text):
            return {"blocked": True, "reason": reason}
    return {"blocked": False, "reason": ""}


# ========== 語氣分類 ==========
def classify_tone(text: str, max_retries=3):
    prompt = f"""
請判斷下面句子的語氣，從以下標籤中多選（可多選）：
{", ".join(TAGS)}

句子：{text}

請只輸出純 JSON array，例如：
["開心","輕鬆"]
"""

    for attempt in range(max_retries):
        try:
            resp = genai.GenerativeModel(MODEL).generate_content(prompt)
            return json.loads(resp.text)
        except Exception as e:
            print(f"API error: {e} (retry {attempt+1})")
            time.sleep(3)

    return []  # 如果失敗，回傳空列表


# ========== checkpoint loader ==========
def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}


# ========== Logger 初始化 ==========
def init_log():
    try:
        with open(LOG_FILE, "x", newline="", encoding="utf8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "text", "blocked", "reason", "tones"])
    except FileExistsError:
        pass  # 已存在時不新建


def log_record(text, blocked, reason, tones):
    with open(LOG_FILE, "a", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            text,
            blocked,
            reason,
            json.dumps(tones, ensure_ascii=False)
        ])


# ========== 主程式 ==========
init_log()

# 讀進原始資料
with open(INPUT_FILE, "r", encoding="utf8") as f:
    data = json.load(f)

# 載入 checkpoint（可中斷續跑）
checkpoint = load_checkpoint()
cache = checkpoint.get("cache", {})
start_index = checkpoint.get("index", 0)

print(f"從第 {start_index} 筆開始（自動續跑）")

api_calls = 0

for i in tqdm(range(start_index, len(data))):
    item = data[i]
    text = item["text"]

    # ---- 檢查屏蔽 ----
    blk = is_blocked(text)
    if blk["blocked"]:
        item["tones"] = []
        log_record(text, True, blk["reason"], [])
        continue

    # ---- 避免重複 ----
    if text in cache:
        item["tones"] = cache[text]
        log_record(text, False, "", cache[text])
        continue

    # ---- API Rate limit: 每 100 次休息 ----
    if api_calls > 0 and api_calls % 100 == 0:
        print("API 使用達 100 次 → 休息 60 秒")
        time.sleep(60)

    # ---- 語氣分類 ----
    tones = classify_tone(text)
    item["tones"] = tones

    cache[text] = tones
    api_calls += 1

    # ---- Logger ----
    log_record(text, False, "", tones)

    # ---- 每 SAVE_INTERVAL 筆儲存 checkpoint ----
    if (i + 1) % SAVE_INTERVAL == 0:
        with open(CHECKPOINT_FILE, "w", encoding="utf8") as f:
            json.dump({"index": i + 1, "cache": cache}, f, ensure_ascii=False, indent=2)
        print(f"Checkpoint saved at index {i+1}")

# 結束後儲存完整結果
with open(OUTPUT_FILE, "w", encoding="utf8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("🚀 全部完成！")
