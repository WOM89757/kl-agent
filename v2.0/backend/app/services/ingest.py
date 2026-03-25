import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument
from sqlalchemy.orm import Session

from app.config import CHROMA_COLLECTION, CHROMA_DIR
from app.logger import get_logger
from app.models.document import Document
from app.services.chunking.models import Block, Chunk
from app.services.chunking.router import chunk_document
from app.services.llm import embedding_model
from app.services.parsing import parse_file
from app.services.retrieval.bm25_store import bm25_retriever

logger = get_logger(__name__)

vector_store = Chroma(
    collection_name=CHROMA_COLLECTION,
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_DIR),
)
logger.info("Vector store initialized")


def sanitize_metadata(metadata: Dict) -> Dict:
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


def build_lc_documents(blocks: list, file_name: str, doc_id: str) -> list:
    chunks = chunk_document(blocks)
    logger.info(f"Chunked into {len(chunks)} chunks")

    docs = []
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
        docs.append(LCDocument(page_content=chunk.text, metadata=metadata))

    return docs


def ingest_file(path: Path, db: Session, file_size: int = 0) -> Document:
    logger.info(f"Ingesting: {path}")

    blocks = parse_file(path)
    if not blocks:
        raise ValueError("文档没有可提取的结构化内容")

    doc_id = str(uuid.uuid4())
    lc_docs = build_lc_documents(blocks=blocks, file_name=path.name, doc_id=doc_id)

    if not lc_docs:
        raise ValueError("文档没有生成可入库的分块")

    ids = [f"{doc_id}:{i}" for i in range(len(lc_docs))]
    vector_store.add_documents(documents=lc_docs, ids=ids)
    logger.info(f"Added {len(lc_docs)} chunks to vector store")

    doc = Document(
        doc_id=doc_id,
        file_name=path.name,
        file_path=str(path),
        file_type=path.suffix.lower().lstrip("."),
        file_size=file_size,
        chunks=len(lc_docs),
        uploaded_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    bm25_retriever.refresh()
    logger.info(f"Ingestion complete: {path.name}, chunks={len(lc_docs)}")
    return doc


def delete_document_by_id(doc_id: str, db: Session) -> Dict:
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise ValueError("文档不存在")

    chunk_count = doc.chunks
    ids = [f"{doc_id}:{i}" for i in range(chunk_count)]

    try:
        vector_store.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} chunks from vector store")
    except Exception as e:
        logger.warning(f"Vector store delete error: {e}")

    file_path = Path(doc.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"File delete error: {e}")

    db.delete(doc)
    db.commit()

    bm25_retriever.refresh()
    return {"message": "删除成功", "doc_id": doc_id}
