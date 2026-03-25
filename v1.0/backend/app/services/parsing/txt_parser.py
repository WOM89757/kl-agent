from typing import List
from app.services.parsing.base import BaseParser
from app.services.chunking.models import Block


class TxtParser(BaseParser):
    def parse(self, file_path: str) -> List[Block]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        blocks = []
        for part in text.split("\n\n"):
            t = part.strip()
            if not t:
                continue
            blocks.append(Block(type="paragraph", text=t))
        return blocks