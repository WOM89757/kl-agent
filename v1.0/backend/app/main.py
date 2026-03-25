import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import UPLOAD_DIR
from app.logger import get_logger

logger = get_logger(__name__)
from app.schemas import (
    AskRequest,
    AskResponse,
    DeleteResponse,
    DocumentInfo,
    UploadResponse,
)
from app.services.agent import answer_question
from app.services.ingest import ingest_file, delete_document_by_id
from app.services.retrieval.base import retrieve_candidates, docs_to_sources
from app.services.storage import load_meta
from app.services.workflow import run_rag_workflow

app = FastAPI(title="Private KB QA Project")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Private KB QA Project is running"}


@app.get("/health")
def health():
    logger.debug("Health check endpoint called")
    return {"status": "ok"}


@app.get("/documents", response_model=List[DocumentInfo])
def list_documents():
    logger.info("Listing all documents")
    docs = load_meta()
    logger.info(f"Found {len(docs)} documents")
    return docs


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    logger.info(f"Received upload request: {file.filename}")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".pdf", ".txt", ".md", ".docx"]:
        logger.warning(f"Invalid file type rejected: {file.filename}, suffix: {suffix}")
        raise HTTPException(status_code=400, detail="仅支持 pdf/txt/md/docx")

    target = UPLOAD_DIR / file.filename
    with open(target, "wb") as f:
        shutil.copyfileobj(file.file, f)
    logger.info(f"File saved to {target}")

    try:
        record = ingest_file(target)
        logger.info(f"File ingested successfully: {file.filename}, doc_id: {record['doc_id']}")
        return {"message": "上传并入库成功", "document": record}
    except Exception as e:
        logger.error(f"Failed to ingest file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"入库失败：{e}")


@app.delete("/documents/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str):
    logger.info(f"Delete request for doc_id: {doc_id}")
    try:
        result = delete_document_by_id(doc_id)
        logger.info(f"Document deleted successfully: {doc_id}")
        return result
    except ValueError as e:
        logger.warning(f"Document not found: {doc_id} - {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        logger.warning("Ask request with empty question")
        raise HTTPException(status_code=400, detail="问题不能为空")

    logger.info(f"Processing question: {question[:100]}...")
    try:
        # answer, docs = answer_question(question)
        # docs = retrieve_candidates(question, top_k=req.top_k)
        # sources = docs_to_sources(docs)
        result = run_rag_workflow(question, req.top_k)
        answer=result["answer"]
        sources = result["sources"][: req.top_k]
        logger.info(f"Question answered successfully, retrieved {len(sources)} sources")
        return AskResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"Failed to answer question '{question[:50]}...': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"问答失败：{e}")