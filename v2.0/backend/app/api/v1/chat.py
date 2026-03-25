from fastapi import APIRouter, HTTPException
from app.logger import get_logger
from app.schemas.chat import AskRequest, AskResponse, Source
from app.services.workflow import run_rag_workflow

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    logger.info(f"Ask: {question[:80]}")
    try:
        result = run_rag_workflow(
            question=question,
            top_k=req.top_k,
            image_base64=req.image_base64,
            media_type=req.media_type,
        )
        sources = [Source(**s) for s in result["sources"][: req.top_k]]
        return AskResponse(
            answer=result["answer"],
            sources=sources,
            rewritten_query=result.get("rewritten_query"),
        )
    except Exception as e:
        logger.error(f"Ask failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"问答失败：{e}")
