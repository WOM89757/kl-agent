import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.logger import get_logger
from app.config import CHROMA_COLLECTION, CHROMA_DIR
from app.services.llm import embedding_model
from app.services.storage import load_meta, save_meta

from app.services.parsing import parse_file
from app.services.chunking.router import chunk_document
from app.services.chunking.models import Block, Chunk
from app.services.storage_chunks import load_chunks_store, save_chunks_store
from app.services.retrieval.bm25_store import bm25_retriever


logger = get_logger(__name__)


vector_store = Chroma(
    collection_name=CHROMA_COLLECTION,
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_DIR),
)
logger.info("Vector store initialized")


def sanitize_metadata(metadata: Dict) -> Dict:
    """
    将 metadata 清洗成 Chroma 可接受的格式：
    - None -> 删除
    - 空 list -> 删除
    - 非空 list -> 转成字符串
    - dict -> 转成字符串
    - 其他基础类型原样保留
    """
    cleaned: Dict = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, list):
            if not value:
                continue
            cleaned[key] = " > ".join(str(x) for x in value)
            continue

        if isinstance(value, dict):
            if not value:
                continue
            cleaned[key] = str(value)
            continue

        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
            continue

        cleaned[key] = str(value)

    return cleaned


def build_documents_from_blocks(blocks: List[Block], file_name: str, doc_id: str) -> List[Document]:
    logger.debug(f"Building documents from blocks for file: {file_name}, doc_id: {doc_id}")

    chunks: List[Chunk] = chunk_document(blocks)
    logger.info(f"Chunked into {len(chunks)} chunks")

    docs: List[Document] = []
    for i, chunk in enumerate(chunks):
        raw_metadata = {
            "doc_id": doc_id,
            "file_name": file_name,
            "source": file_name,
            "chunk_index": i,
            "chunk_id": f"{doc_id}:{i}",
            **(chunk.metadata or {}),
        }
        metadata = sanitize_metadata(raw_metadata)

        docs.append(
            Document(
                page_content=chunk.text,
                metadata=metadata,
            )
        )

    logger.info(f"Built {len(docs)} LangChain documents")
    return docs


def ingest_file(path: Path) -> Dict:
    logger.info(f"Starting ingestion for file: {path}")

    blocks = parse_file(path)
    if not blocks:
        logger.warning(f"No structured blocks extracted from file: {path}")
        raise ValueError("文档没有可提取的结构化内容")

    logger.info(f"Parsed {len(blocks)} blocks from file: {path.name}")

    doc_id = str(uuid.uuid4())
    logger.debug(f"Generated doc_id: {doc_id}")

    docs = build_documents_from_blocks(
        blocks=blocks,
        file_name=path.name,
        doc_id=doc_id,
    )
    if not docs:
        logger.warning(f"No chunks generated from file: {path}")
        raise ValueError("文档没有生成可入库的分块")

    chunk_store = load_chunks_store()
    for i, doc in enumerate(docs):
        chunk_store.append(
            {
                "id": f"{doc_id}:{i}",
                "doc_id": doc_id,
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
        )
    save_chunks_store(chunk_store)

    ids = [f"{doc_id}:{i}" for i in range(len(docs))]

    logger.info(f"Adding {len(docs)} document chunks to vector store")
    logger.info(f"First document metadata: {docs[0].metadata if docs else {}}")
    vector_store.add_documents(documents=docs, ids=ids)
    logger.debug(f"Added documents with IDs: {ids[:3]}...")

    logger.info(f"Parsed blocks: {len(blocks)}")
    logger.info(f"First 5 block types: {[b.type for b in blocks[:5]]}")
    logger.info(f"Chunk strategies: {[d.metadata.get('strategy') for d in docs[:5]]}")


    meta = load_meta()
    record = {
        "doc_id": doc_id,
        "file_name": path.name,
        "file_path": str(path),
        "chunks": len(docs),
        "uploaded_at": datetime.now().isoformat(),
    }
    meta.append(record)
    save_meta(meta)
    bm25_retriever.refresh()

    logger.info(f"File ingestion completed: {path.name}, {len(docs)} chunks")
    return record


def delete_document_by_id(doc_id: str) -> Dict:
    logger.info(f"Starting deletion for doc_id: {doc_id}")
    meta = load_meta()
    target = next((x for x in meta if x["doc_id"] == doc_id), None)
    if not target:
        logger.warning(f"Document not found for deletion: {doc_id}")
        raise ValueError("文档不存在")

    chunk_count = int(target["chunks"])
    ids = [f"{doc_id}:{i}" for i in range(chunk_count)]

    logger.info(f"Preparing to delete {len(ids)} chunks from Chroma")
    logger.debug(f"IDs to delete: {ids[:5]}{'...' if len(ids) > 5 else ''}")

    try:
        collection = vector_store._client.get_collection(CHROMA_COLLECTION)
        result = collection.get(ids=ids)
        existing_count = len(result["ids"]) if result else 0
        logger.info(f"Found {existing_count}/{len(ids)} chunks in Chroma")
    except Exception as e:
        logger.warning(f"Failed to query before deletion: {e}")
        collection = None

    logger.debug("Calling vector_store.delete()")
    vector_store.delete(ids=ids)
    logger.info("Called vector_store.delete()")

    if collection is not None:
        try:
            result = collection.get(ids=ids)
            remaining_count = len(result["ids"]) if result else 0
            logger.info(f"Remaining chunks in Chroma after deletion: {remaining_count}")
        except Exception as e:
            logger.warning(f"Failed to query after deletion: {e}")

    new_meta = [x for x in meta if x["doc_id"] != doc_id]
    save_meta(new_meta)
    logger.debug("Updated metadata file")

    file_path = Path(target["file_path"])
    if file_path.exists():
        try:
            logger.info(f"Deleting physical file: {file_path}")
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")

    logger.info(f"Document deletion completed: {doc_id}")
    bm25_retriever.refresh()

    return {"message": "删除成功", "doc_id": doc_id}