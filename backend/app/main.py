"""
AI Autonomous Testing Agent - FastAPI Main Application Entry Point

This module initializes the FastAPI application with all middleware, 
routers, event handlers, and global exception handling.
"""

import asyncio
import sys
import time
import uuid
from contextlib import asynccontextmanager

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import settings
from app.database import init_db, close_db
from app.utils.logger import setup_logging
from app.utils.exceptions import AppException


# ─── Application Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handlers."""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    
    # Setup logging
    setup_logging()
    
    # Initialize storage directories
    settings.screenshots_path
    settings.videos_path
    settings.logs_path
    settings.reports_path
    settings.generated_scripts_path
    logger.info("📁 Storage directories initialized")
    
    # Initialize database
    await init_db()
    logger.info("🐘 Database tables initialized")
    
    # Install Playwright browsers
    try:
        import subprocess
        subprocess.run(
            ["playwright", "install", "chromium"],
            capture_output=True,
            timeout=120,
        )
        logger.info("🎭 Playwright browsers installed")
    except Exception as e:
        logger.warning(f"⚠️ Playwright browser install skipped: {e}")
    
    logger.info("✅ Application startup complete")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    await close_db()
    logger.info("👋 Shutdown complete")


# ─── FastAPI App Instance ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## AI Autonomous Testing Agent API

    A production-ready AI-powered testing platform that automatically:
    - 🔍 **Discovers** web application structure and elements
    - 🧠 **Analyzes** pages using AI (GPT-4o / Gemini)
    - 📝 **Generates** comprehensive test cases (functional, UI, security, performance)
    - 🎭 **Creates** Playwright automation scripts with Page Object Model
    - ⚡ **Executes** tests autonomously with self-healing locators
    - 🔬 **Analyzes** failures using AI root cause analysis
    - 📊 **Reports** via Allure, Excel, and PDF formats
    
    ### Multi-Agent Architecture
    The system uses 8 specialized AI agents coordinated by LangChain.
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ─── Middleware ────────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


# ─── Request ID & Timing Middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    """Add request ID and process time to all responses."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} [{process_time:.3f}s] "
            f"[{request_id[:8]}]"
        )
        return response
    except Exception as exc:
        process_time = time.perf_counter() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"[{process_time:.3f}s] [{request_id[:8]}] - {exc}"
        )
        raise


# ─── Global Exception Handlers ────────────────────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.error(f"AppException: {exc.detail} | Code: {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ─── Static Files ─────────────────────────────────────────────────────────────────
import os
storage_path = settings.STORAGE_PATH
if not os.path.exists(storage_path):
    os.makedirs(storage_path, exist_ok=True)

app.mount("/storage", StaticFiles(directory=storage_path), name="storage")


# ─── API Routers ──────────────────────────────────────────────────────────────────
from app.api.v1 import projects, runs, reports, chat, websocket, files

API_PREFIX = "/api/v1"

app.include_router(projects.router, prefix=API_PREFIX, tags=["Projects"])
app.include_router(runs.router, prefix=API_PREFIX, tags=["Test Runs"])
app.include_router(reports.router, prefix=API_PREFIX, tags=["Reports"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["AI Chat"])
app.include_router(files.router, prefix=API_PREFIX, tags=["Files"])
app.include_router(websocket.router, prefix="", tags=["WebSocket"])


# ─── Health Check ─────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "service": settings.APP_NAME,
    }


@app.get("/api/v1/info", tags=["Health"])
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_provider": settings.AI_PROVIDER,
        "browser": settings.BROWSER_TYPE,
        "max_crawl_pages": settings.MAX_CRAWL_PAGES,
        "features": [
            "Application Discovery",
            "AI Page Analysis",
            "Test Case Generation",
            "Playwright Script Generation",
            "Self-Healing Locators",
            "Autonomous Execution",
            "Failure Analysis",
            "Visual Testing",
            "AI Chat Assistant",
            "Allure/Excel/PDF Reports",
        ],
    }


@app.get("/api/v1/dashboard/stats", tags=["Dashboard"])
async def dashboard_stats():
    """
    Aggregated dashboard statistics.
    Computes totals from the SQLite database in real-time.
    Called by the frontend Refresh button and initial load.
    """
    from app.database import AsyncSessionLocal
    from app.models.project import Project
    from app.models.test_run import TestRun
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        try:
            # Total projects
            proj_count = await session.scalar(select(func.count()).select_from(Project))

            # Total runs
            run_count = await session.scalar(select(func.count()).select_from(TestRun))

            # Aggregate passes / failures across all runs
            total_passed = await session.scalar(
                select(func.coalesce(func.sum(TestRun.passed), 0))
            )
            total_failed = await session.scalar(
                select(func.coalesce(func.sum(TestRun.failed), 0))
            )
            total_skipped = await session.scalar(
                select(func.coalesce(func.sum(TestRun.skipped), 0))
            )
            total_tests = int(total_passed or 0) + int(total_failed or 0) + int(total_skipped or 0)
            pass_rate = round((int(total_passed or 0) / total_tests * 100) if total_tests > 0 else 0, 1)

            # Active / running projects
            active_count = await session.scalar(
                select(func.count()).select_from(Project).where(Project.status.in_(["discovering", "running"]))
            )

            logger.info(
                f"📊 Dashboard stats: {proj_count} projects | {run_count} runs | "
                f"{pass_rate}% pass rate"
            )

            return {
                "total_projects": int(proj_count or 0),
                "total_runs": int(run_count or 0),
                "total_passed": int(total_passed or 0),
                "total_failed": int(total_failed or 0),
                "total_skipped": int(total_skipped or 0),
                "total_tests": total_tests,
                "overall_pass_rate": pass_rate,
                "active_projects": int(active_count or 0),
            }
        except Exception as e:
            logger.error(f"Dashboard stats error: {e}")
            return {
                "total_projects": 0,
                "total_runs": 0,
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "total_tests": 0,
                "overall_pass_rate": 0,
                "active_projects": 0,
            }


