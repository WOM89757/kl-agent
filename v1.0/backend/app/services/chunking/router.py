from typing import List
from app.services.chunking.models import Block, Chunk
from app.services.chunking.classifier import classify_document
from app.services.chunking.generic_chunker import generic_chunk
from app.services.chunking.policy_chunker import policy_chunk
from app.services.chunking.faq_chunker import faq_chunk
from app.logger import get_logger
logger = get_logger(__name__)


def chunk_document(blocks: List[Block]) -> List[Chunk]:
    doc_type = classify_document(blocks)
    logger.info(f"Document type: {doc_type}")
    if doc_type == "policy":
        return policy_chunk(blocks)

    if doc_type == "faq":
        return faq_chunk(blocks)

    # table_heavy / structured / generic 先都走通用策略
    return generic_chunk(blocks)