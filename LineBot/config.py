# LINE Bot 設定
import os
from pathlib import Path
from dotenv import load_dotenv

# 載入上層資料夾的 .env 檔案
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')