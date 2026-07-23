import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from kernel.common.config import get_settings
from kernel.common.database import engine, Base
from kernel.common.exceptions import BusinessException
from kernel.common.response import error_response
from kernel.sisyphus.orchestrator import SisyphusOrchestrator
from agents import register_all_agents

settings = get_settings()
app = FastAPI(title=settings.app_name)
orchestrator = SisyphusOrchestrator()
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_startup_completed = False


@app.exception_handler(BusinessException)
async def business_exception_handler(_request: Request, exc: BusinessException):
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.message))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=error_response(str(exc)))


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(_request: Request, exc: IntegrityError):
    logger.error("IntegrityError: %s", exc)
    return JSONResponse(status_code=400, content=error_response("数据库操作异常"))


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=(type(exc), exc, exc.__traceback__))
    return JSONResponse(status_code=500, content=error_response("服务器内部错误"))


@app.on_event("startup")
async def startup():
    global _startup_completed
    if _startup_completed:
        return
    Base.metadata.create_all(bind=engine)
    register_all_agents(orchestrator)
    for agent in orchestrator.agents.values():
        agent.on_startup()
    orchestrator.mount_to_app(app)
    _startup_completed = True
    logger.info("[System] All %d agents registered. Sisyphus orchestrator ready.", len(orchestrator.agents))


if FRONTEND_DIR.exists():
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")


@app.get("/demo")
def demo_page(request: Request):
    return RedirectResponse(url="/ui/")


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs", "ui": "/ui/", "demo": "/demo"}
