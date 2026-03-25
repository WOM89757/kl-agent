from pathlib import Path
from typing import List

from app.logger import get_logger
from app.services.chunking.models import Block
from app.services.parsing.txt_parser import TxtParser
from app.services.parsing.docx_parser import DocxParser
from app.services.parsing.pdf_parser import PdfParser

logger = get_logger(__name__)


def parse_file(path: Path) -> List[Block]:
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return TxtParser().parse(path)

    if suffix == ".docx":
        return DocxParser().parse(path)

    if suffix == ".pdf":
        return PdfParser(path)

    raise ValueError(f"不支持的文件类型: {suffix}")
