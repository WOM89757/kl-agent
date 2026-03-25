import re
from typing import List
from app.services.chunking.models import Block, Chunk


def faq_chunk(blocks: List[Block]) -> List[Chunk]:
    text = "\n".join(b.text for b in blocks if b.text.strip())
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    chunks = []
    current = []

    for line in lines:
        if re.match(r"^(问|Q)[:：]", line) and current:
            chunks.append(Chunk(text="\n".join(current), metadata={"strategy": "faq"}))
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append(Chunk(text="\n".join(current), metadata={"strategy": "faq"}))
    return chunks
