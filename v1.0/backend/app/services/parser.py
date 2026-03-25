from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument

from app.logger import get_logger

logger = get_logger(__name__)


def read_txt(path: Path) -> str:
    logger.debug(f"Reading TXT file: {path}")
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        logger.info(f"Read TXT file successfully: {len(content)} chars")
        return content
    except Exception as e:
        logger.error(f"Failed to read TXT file {path}: {e}", exc_info=True)
        raise


def read_pdf(path: Path) -> str:
    logger.debug(f"Reading PDF file: {path}")
    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append(text)
            logger.debug(f"Extracted page {i+1}/{len(reader.pages)}: {len(text)} chars")
        content = "\n".join(pages)
        logger.info(f"Read PDF file successfully: {len(content)} chars from {len(pages)} pages")
        return content
    except Exception as e:
        logger.error(f"Failed to read PDF file {path}: {e}", exc_info=True)
        raise


def read_docx(path: Path) -> str:
    logger.debug(f"Reading DOCX file: {path}")
    try:
        doc = DocxDocument(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        content = "\n".join(paragraphs)
        logger.info(f"Read DOCX file successfully: {len(content)} chars from {len(paragraphs)} paragraphs")
        return content
    except Exception as e:
        logger.error(f"Failed to read DOCX file {path}: {e}", exc_info=True)
        raise


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    logger.debug(f"Extracting text from file: {path}, suffix: {suffix}")
    if suffix in [".txt", ".md"]:
        logger.info(f"Extracting text from TXT/MD file: {path.name}")
        return read_txt(path)
    if suffix == ".pdf":
        logger.info(f"Extracting text from PDF file: {path.name}")
        return read_pdf(path)
    if suffix == ".docx":
        logger.info(f"Extracting text from DOCX file: {path.name}")
        return read_docx(path)
    logger.error(f"Unsupported file type: {suffix}")
    raise ValueError(f"不支持的文件类型：{suffix}")