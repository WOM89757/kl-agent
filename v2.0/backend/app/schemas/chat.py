from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Source(BaseModel):
    file_name: Optional[str] = None
    doc_id: Optional[str] = None
    chunk_index: Optional[int] = None
    preview: Optional[str] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    image_base64: Optional[str] = None   # base64 encoded image for multimodal
    media_type: Optional[str] = None     # image/jpeg, image/png, etc.


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    rewritten_query: Optional[str] = None
