from typing import List, Dict, Any
from langchain_core.documents import Document

from app.logger import get_logger
from app.config import MAX_RETRIEVAL_K
from app.services.retrieval.hybrid_retriever import hybrid_retrieve

logger = get_logger(__name__)


def retrieve_candidates(query: str, top_k: int = MAX_RETRIEVAL_K) -> List[Document]:
    candidates = hybrid_retrieve(query, top_k=top_k)
    logger.info(f"Retrieved {len(candidates)} documents for query")
    return candidates


def docs_to_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    sources = []
    for d in docs:
        sources.append({
            "file_name": d.metadata.get("file_name"),
            "doc_id": d.metadata.get("doc_id"),
            "chunk_index": d.metadata.get("chunk_index"),
            "preview": d.page_content,
        })
    return sources
