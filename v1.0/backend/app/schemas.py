from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = 5


class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class DocumentInfo(BaseModel):
    doc_id: str
    file_name: str
    file_path: str
    chunks: int
    uploaded_at: str


class UploadResponse(BaseModel):
    message: str
    document: DocumentInfo


class DeleteResponse(BaseModel):
    message: str
    doc_id: str