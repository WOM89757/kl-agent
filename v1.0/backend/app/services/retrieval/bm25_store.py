import re
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from app.logger import get_logger
from app.config import CHROMA_COLLECTION, CHROMA_DIR
from app.services.llm import embedding_model
from langchain_chroma import Chroma

logger = get_logger(__name__)


vector_store = Chroma(
    collection_name=CHROMA_COLLECTION,
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_DIR),
)


def tokenize_zh(text: str) -> List[str]:
    """
    轻量中文分词：
    - 保留中文连续串
    - 保留数字/英文串
    - 适合制度问答里的“1年、10年、5天、年假”这类查询
    """
    text = (text or "").lower().strip()
    return re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text)


def expand_query(query: str) -> str:
    """
    轻量 query 扩展，先解决常见同义词问题
    """
    q = query.strip()

    synonym_map = {
        "年假": ["年休假", "带薪年休假"],
        "病假": ["请病假"],
        "事假": ["请事假"],
        "调休": ["补休"],
        "离职": ["解除劳动关系", "终止劳动关系"],
        "加班": ["延时工作"],
    }

    for word, syns in synonym_map.items():
        if word in q:
            for s in syns:
                if s not in q:
                    q += f" {s}"

    return q


class BM25Retriever:
    def __init__(self):
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25 = None
        self.refresh()

    def refresh(self):
        """
        从 Chroma 全量拉取文档，构建 BM25 索引
        适合中小规模知识库；后续量大了再单独做倒排存储
        """
        logger.info("Refreshing BM25 index from Chroma")

        all_data = vector_store.get(include=["documents", "metadatas"])
        docs = all_data.get("documents", []) or []
        metas = all_data.get("metadatas", []) or []

        self.documents = [
            Document(page_content=doc, metadata=meta or {})
            for doc, meta in zip(docs, metas)
        ]
        self.tokenized_corpus = [tokenize_zh(d.page_content) for d in self.documents]

        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 index ready, documents={len(self.documents)}")
        else:
            self.bm25 = None
            logger.warning("BM25 index is empty")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.documents:
            return []

        q = expand_query(query)
        query_tokens = tokenize_zh(q)

        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        results: List[Dict[str, Any]] = []
        for idx, score in ranked:
            doc = self.documents[idx]
            results.append(
                {
                    "doc": doc,
                    "score": float(score),
                    "retrieval": "bm25",
                }
            )
        return results


bm25_retriever = BM25Retriever()