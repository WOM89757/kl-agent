# app/services/storage_chunks.py
import json
from pathlib import Path
from typing import List, Dict

CHUNKS_FILE = Path("app/data/chunks_store.json")


def load_chunks_store() -> List[Dict]:
    if not CHUNKS_FILE.exists():
        return []
    return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))


def save_chunks_store(items: List[Dict]) -> None:
    CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHUNKS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )