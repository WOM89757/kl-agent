from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, BigInteger
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), unique=True, index=True, nullable=False)
    file_name = Column(String(512), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(16), nullable=False)
    file_size = Column(BigInteger, default=0)
    chunks = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
