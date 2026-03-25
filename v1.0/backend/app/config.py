import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
META_PATH = DATA_DIR / "documents.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "local-dev-key")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:40051/v1")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "qwen2.5-14b-instruct")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "bge-m3")
OPENAI_EMBEDDING_URL = os.getenv("OPENAI_EMBEDDING_URL", "http://127.0.0.1:40051/v1")

CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "private_kb")
MAX_RETRIEVAL_K = int(os.getenv("MAX_RETRIEVAL_K", "6"))

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_DIR = BASE_DIR.parent / "logs"