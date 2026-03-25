from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.logger import get_logger
from app.config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_CHAT_MODEL,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_URL
)

logger = get_logger(__name__)

# 连接本地 OpenAI API 兼容服务
logger.info(f"Initializing Chat LLM with model: {OPENAI_CHAT_MODEL}")
chat_llm = ChatOpenAI(
    model=OPENAI_CHAT_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0.2,
    timeout=120,
)
logger.debug("Chat LLM initialized successfully")

logger.info(f"Initializing Embedding model: {OPENAI_EMBEDDING_MODEL}")
embedding_model = OpenAIEmbeddings(
    model=OPENAI_EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_EMBEDDING_URL,
)
logger.debug("Embedding model initialized successfully")