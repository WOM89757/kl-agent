import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.logger import get_logger
from app.models.document import Document
from app.schemas.document import (
    DeleteResponse,
    DocumentInfo,
    DocumentList,
    DocumentUpdate,
    UploadResponse,
)
from app.services.ingest import ingest_file, delete_document_by_id

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_TYPES = {".pdf", ".txt", ".md", ".docx"}


@router.get("", response_model=DocumentList)
def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Document)
    if keyword:
        query = query.filter(Document.file_name.ilike(f"%{keyword}%"))

    total = query.count()
    items = (
        query.order_by(Document.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return DocumentList(total=total, items=items)


@router.get("/{doc_id}", response_model=DocumentInfo)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.post("", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 pdf/txt/md/docx")

    target = UPLOAD_DIR / file.filename
    with open(target, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = target.stat().st_size

    try:
        record = ingest_file(path=target, db=db, file_size=file_size)
        return UploadResponse(message="上传并入库成功", document=record)
    except Exception as e:
        logger.error(f"Ingest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"入库失败：{e}")


@router.patch("/{doc_id}", response_model=DocumentInfo)
def update_document(
    doc_id: str,
    body: DocumentUpdate,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if body.description is not None:
        doc.description = body.description

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    try:
        result = delete_document_by_id(doc_id=doc_id, db=db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
