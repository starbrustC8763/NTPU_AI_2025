#Get Picture at https://mypic.0m0.uk/images/{season}/{episode}/{frame_prefer}.webp
import json
import requests
import os

# === 設定 ===
json_path = "mygo/mygo_data.json"  # 你的 JSON 檔案
base_url = "https://mypic.0m0.uk/images"  # 圖片資料庫主網址
download_dir = "mygo_images"  # 如果要下載圖片，存在這裡

# === 讀取 JSON ===
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

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

# === 測試 ===
if __name__ == "__main__":
    user_text = input("請輸入要查找的表情文字：").strip()
    find_image_by_text(user_text, download=True)
