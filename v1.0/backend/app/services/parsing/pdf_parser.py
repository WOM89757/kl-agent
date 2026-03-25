from pathlib import Path
from typing import List
from pypdf import PdfReader

from app.services.chunking.models import Block


def PdfParser(path: Path) -> List[Block]:
    reader = PdfReader(str(path))
    blocks: List[Block] = []

    for page_no, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue

        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        for part in parts:
            blocks.append(Block(type="paragraph", text=part, page=page_no))

    return blocks