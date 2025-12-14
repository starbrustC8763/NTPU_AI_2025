from google.generativeai import embed_content
import faiss
import numpy as np
import json

EMB_MODEL = "text-embedding-004"

with open("mygo_labeled.json", "r", encoding="utf8") as f:
    data = json.load(f)

embs = []
for d in data:
    emb = embed_content(model=EMB_MODEL, content=d["text"])["embedding"]
    embs.append(emb)

emb_matrix = np.array(embs).astype("float32")

# 建立向量索引
index = faiss.IndexFlatL2(emb_matrix.shape[1])
index.add(emb_matrix)

faiss.write_index(index, "mygo.index")
