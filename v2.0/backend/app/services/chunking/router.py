import logging
from typing import List
from app.services.chunking.models import Block, Chunk
from app.services.chunking.classifier import classify_document
from app.services.chunking.generic_chunker import generic_chunk
from app.services.chunking.faq_chunker import faq_chunk

logger = logging.getLogger(__name__)


def chunk_document(blocks: List[Block]) -> List[Chunk]:
    doc_type = classify_document(blocks)
    logger.info(f"Document type: {doc_type}")

    if doc_type == "faq":
        return faq_chunk(blocks)

    # policy, structured, table_heavy, generic -> use generic chunker
    # (policy_chunker can be imported separately if needed)
    return generic_chunk(blocks)
