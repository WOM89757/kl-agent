from typing import List, Dict, Any

from langchain_core.documents import Document

from app.logger import get_logger
from app.config import MAX_RETRIEVAL_K
from app.services.retrieval.bm25_store import bm25_retriever, expand_query
from app.services.llm import embedding_model
from app.config import CHROMA_COLLECTION, CHROMA_DIR
from langchain_chroma import Chroma

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

    doc_id = doc.metadata.get("doc_id", "")
    chunk_index = doc.metadata.get("chunk_index", "")
    return f"{doc_id}:{chunk_index}"


def _normalize(items: List[Dict[str, Any]], score_key: str = "score") -> List[Dict[str, Any]]:
    if not items:
        return items

    scores = [x[score_key] for x in items]
    s_min = min(scores)
    s_max = max(scores)

    if s_max == s_min:
        for x in items:
            x["norm_score"] = 1.0
        return items

    for x in items:
        x["norm_score"] = (x[score_key] - s_min) / (s_max - s_min)

    return items


def dense_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    q = expand_query(query)

    # similarity_search_with_score 返回距离，通常越小越相似
    pairs = vector_store.similarity_search_with_score(q, k=top_k)

    results: List[Dict[str, Any]] = []
    for doc, distance in pairs:
        results.append(
            {
                "doc": doc,
                "score": -float(distance),  # 转成越大越好，便于融合
                "retrieval": "dense",
            }
        )
    return results


def hybrid_retrieve(query: str, top_k: int = MAX_RETRIEVAL_K) -> List[Document]:
    dense_hits = dense_search(query, top_k=top_k)
    bm25_hits = bm25_retriever.search(query, top_k=top_k)

    dense_hits = _normalize(dense_hits)
    bm25_hits = _normalize(bm25_hits)

    merged: Dict[str, Dict[str, Any]] = {}

    for item in dense_hits:
        doc = item["doc"]
        key = _doc_key(doc)
        merged[key] = {
            "doc": doc,
            "dense_score": item["norm_score"],
            "bm25_score": 0.0,
        }

    for item in bm25_hits:
        doc = item["doc"]
        key = _doc_key(doc)

        if key in merged:
            merged[key]["bm25_score"] = item["norm_score"]
        else:
            merged[key] = {
                "doc": doc,
                "dense_score": 0.0,
                "bm25_score": item["norm_score"],
            }

    q = query.strip()

    for _, item in merged.items():
        doc = item["doc"]
        text = doc.page_content or ""
        meta = doc.metadata or {}

        hybrid_score = 0.55 * item["dense_score"] + 0.45 * item["bm25_score"]

        # 数字条件加分：制度问答很有用
        if "1年" in q and "10年" in q and "1年" in text and "10年" in text:
            hybrid_score += 0.15

        if ("年假" in q or "年休假" in q) and ("年假" in text or "年休假" in text):
            hybrid_score += 0.08

        # 规则型条款略微加权
        strategy = meta.get("strategy")
        block_type = meta.get("block_type")
        if strategy == "policy_clause" or block_type == "clause":
            hybrid_score += 0.05

        item["hybrid_score"] = hybrid_score

    ranked = sorted(
        merged.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )

    docs = [x["doc"] for x in ranked[:top_k]]

    logger.info(
        "Hybrid retrieved %s docs (dense=%s, bm25=%s)",
        len(docs),
        len(dense_hits),
        len(bm25_hits),
    )

    return docs