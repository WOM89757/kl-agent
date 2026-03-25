from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.logger import get_logger
from app.config import MAX_RETRIEVAL_K, CHROMA_COLLECTION, CHROMA_DIR
from app.services.retrieval.bm25_store import bm25_retriever, expand_query
from app.services.llm import embedding_model

logger = get_logger(__name__)

vector_store = Chroma(
    collection_name=CHROMA_COLLECTION,
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_DIR),
)


def _doc_key(doc: Document) -> str:
    chunk_id = doc.metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    return f"{doc.metadata.get('doc_id', '')}:{doc.metadata.get('chunk_index', '')}"


def _normalize(items: List[Dict[str, Any]], score_key: str = "score") -> List[Dict[str, Any]]:
    if not items:
        return items
    scores = [x[score_key] for x in items]
    s_min, s_max = min(scores), max(scores)
    if s_max == s_min:
        for x in items:
            x["norm_score"] = 1.0
        return items
    for x in items:
        x["norm_score"] = (x[score_key] - s_min) / (s_max - s_min)
    return items


def dense_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    q = expand_query(query)
    pairs = vector_store.similarity_search_with_score(q, k=top_k)
    return [{"doc": doc, "score": -float(distance), "retrieval": "dense"} for doc, distance in pairs]


def hybrid_retrieve(query: str, top_k: int = MAX_RETRIEVAL_K) -> List[Document]:
    dense_hits = _normalize(dense_search(query, top_k=top_k))
    bm25_hits = _normalize(bm25_retriever.search(query, top_k=top_k))

    merged: Dict[str, Dict[str, Any]] = {}
    for item in dense_hits:
        key = _doc_key(item["doc"])
        merged[key] = {"doc": item["doc"], "dense_score": item["norm_score"], "bm25_score": 0.0}

    for item in bm25_hits:
        key = _doc_key(item["doc"])
        if key in merged:
            merged[key]["bm25_score"] = item["norm_score"]
        else:
            merged[key] = {"doc": item["doc"], "dense_score": 0.0, "bm25_score": item["norm_score"]}

    q = query.strip()
    for _, item in merged.items():
        doc = item["doc"]
        text = doc.page_content or ""
        meta = doc.metadata or {}
        score = 0.55 * item["dense_score"] + 0.45 * item["bm25_score"]
        if "1年" in q and "10年" in q and "1年" in text and "10年" in text:
            score += 0.15
        if ("年假" in q or "年休假" in q) and ("年假" in text or "年休假" in text):
            score += 0.08
        if meta.get("strategy") == "policy_clause" or meta.get("block_type") == "clause":
            score += 0.05
        item["hybrid_score"] = score

    ranked = sorted(merged.values(), key=lambda x: x["hybrid_score"], reverse=True)
    docs = [x["doc"] for x in ranked[:top_k]]
    logger.info("Hybrid retrieved %s docs (dense=%s, bm25=%s)", len(docs), len(dense_hits), len(bm25_hits))
    return docs
