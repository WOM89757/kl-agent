import json
from typing import Any, Dict, List

from app.logger import get_logger
from app.config import META_PATH

logger = get_logger(__name__)


def load_meta() -> List[Dict[str, Any]]:
    logger.debug(f"Loading metadata from {META_PATH}")
    if not META_PATH.exists():
        logger.warning(f"Metadata file does not exist: {META_PATH}")
        return []
    try:
        with open(META_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.debug("Metadata file is empty")
                return []
            data = json.loads(content)
            logger.info(f"Loaded {len(data)} document records from metadata")
            return data
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error in metadata file: {e}")
        # 如果 JSON 格式错误，返回空列表
        return []
    except Exception as e:
        logger.error(f"Failed to load metadata: {e}", exc_info=True)
        raise


def save_meta(items: List[Dict[str, Any]]) -> None:
    logger.debug(f"Saving metadata with {len(items)} records to {META_PATH}")
    try:
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        logger.info(f"Metadata saved successfully")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}", exc_info=True)
        raise