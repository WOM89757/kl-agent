from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class DocumentInfo(BaseModel):
    doc_id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    chunks: int
    description: Optional[str] = None
    uploaded_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    description: Optional[str] = None


class DocumentList(BaseModel):
    total: int
    items: list[DocumentInfo]


class UploadResponse(BaseModel):
    message: str
    document: DocumentInfo


class DeleteResponse(BaseModel):
    message: str
    doc_id: str


class DocumentUpdate(BaseModel):
    description: Optional[str] = None
