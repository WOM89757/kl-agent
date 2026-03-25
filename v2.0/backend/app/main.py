from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.v1.router import api_router
from app.database import init_db
from app.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="KL Agent - Private KB QA",
    description="私有知识库问答系统 API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Serve frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

    @app.get("/")
    def serve_chat():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/admin")
    def serve_admin():
        return FileResponse(str(FRONTEND_DIR / "admin.html"))


@app.on_event("startup")
def startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("KL Agent v2.0 started")


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
