import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("環境變數 GEMINI_API_KEY 尚未設定")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")
print("Current working directory:", os.getcwd())
response = model.generate_content("Hello Gemini, respond 'OK'.")
print(response.text)
