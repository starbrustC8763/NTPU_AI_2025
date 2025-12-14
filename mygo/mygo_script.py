#Data is made by https://github.com/Its-MyPic/Its-MyPicDB/blob/json/data.json
import json

input_file = "mygo/mygo_data.json"   # 你的 JSON 檔案名稱
output_file = "mygo/mygo_texts.txt"  # 要輸出的文字檔

# 讀取 JSON 檔
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 提取 text 欄位並去除重複（保留原順序）
seen = set()
texts = []

for item in data:
    if isinstance(item, dict) and "text" in item:
        text_value = str(item["text"]).strip()
        if text_value and text_value not in seen:
            seen.add(text_value)
            texts.append(text_value)

# 寫入 txt 檔
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(texts))

print(f"✅ 已成功擷取 {len(texts)} 筆唯一文字，輸出到 {output_file}")