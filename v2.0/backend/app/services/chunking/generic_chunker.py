from typing import List
from app.services.chunking.models import Block, Chunk


def generic_chunk(blocks: List[Block], max_chars: int = 800, overlap: int = 80) -> List[Chunk]:
    texts = [b.text.strip() for b in blocks if b.text.strip()]
    chunks = []
    current = ""
    current_meta = {"strategy": "generic"}

    for t in texts:
        if len(current) + len(t) + 1 <= max_chars:
            current = f"{current}\n{t}".strip()
        else:
            if current:
                chunks.append(Chunk(text=current, metadata=current_meta.copy()))
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail}\n{t}".strip()

    if current:
        chunks.append(Chunk(text=current, metadata=current_meta.copy()))
    return chunks
