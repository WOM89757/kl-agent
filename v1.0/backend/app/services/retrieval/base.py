from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.logger import get_logger
from app.config import CHROMA_COLLECTION, CHROMA_DIR, MAX_RETRIEVAL_K
from app.services.llm import embedding_model
from app.services.rerank import rerank_with_llm
from app.services.retrieval.hybrid_retriever import hybrid_retrieve


logger = get_logger(__name__)


vector_store = Chroma(
    collection_name=CHROMA_COLLECTION,
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_DIR),
)
logger.debug("Retrieval vector store initialized")


def retrieve_candidates(query: str, top_k: int = MAX_RETRIEVAL_K) -> List[Document]:
    logger.debug(f"Searching for query: {query[:100]}..., top_k={top_k}")

    # all_data = vector_store.get()
    # print("总条数：", len(all_data["documents"]))
    # for i, doc in enumerate(all_data["documents"]):
    #     print(f"\n===== Chunk {i} =====")
    #     print(doc)

    # # candidates = vector_store.similarity_search(query, k=20)
    # candidates = vector_store.similarity_search(query, k=top_k)
    # logger.info(f"Retrieved {len(candidates )} documents for query")

    candidates = hybrid_retrieve(query, top_k=top_k)
    logger.info(f"Retrieved {len(candidates)} documents for query")
    for i, doc in enumerate(candidates[:5]):
        logger.info(
            "Top %s -> chunk=%s, file=%s, preview=%s",
            i + 1,
            doc.metadata.get("chunk_index"),
            doc.metadata.get("file_name"),
            doc.page_content[:120].replace("\n", " "),
        )

    # logger.info(f"Retrieved documents: {reranked[:]}...")
    return candidates


def serialize_docs(docs: List[Document]) -> str:
    logger.debug(f"Serializing {len(docs)} documents")
    blocks = []
    for d in docs:
        meta = d.metadata
        blocks.append(
            "\n".join(
                [
                    f"文件：{meta.get('file_name', '')}",
                    f"文档 ID: {meta.get('doc_id', '')}",
                    f"分块序号：{meta.get('chunk_index', '')}",
                    f"内容：{d.page_content}",
                ]
            )
        )
    logger.debug(f"Serialized content length: {sum(len(b) for b in blocks)} chars")
    return "\n\n---\n\n".join(blocks)


def docs_to_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    logger.debug(f"Converting {len(docs)} documents to sources")
    sources = []
    for d in docs:
        sources.append(
            {
                "file_name": d.metadata.get("file_name"),
                "doc_id": d.metadata.get("doc_id"),
                "chunk_index": d.metadata.get("chunk_index"),
                "preview": d.page_content[:],
                # "preview": d.page_content[:300],
            }
        )
    logger.debug(f"Converted to {len(sources)} sources")
    return sources