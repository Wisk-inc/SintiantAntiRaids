import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
PREFERRED_MODEL = os.getenv("MODEL", "auto")

RAID_THRESHOLD_SEC = 10
CHANNEL_DELETE_LIMIT = 3
ROLE_DELETE_LIMIT = 3
BAN_LIMIT = 3
MSG_CACHE_SIZE = 500
SNAPSHOT_INTERVAL_MS = 300000 # 5 minutes
