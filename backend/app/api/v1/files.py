"""
FastAPI router for serving stored test artifact files.

Endpoints:
    GET /files/screenshots/{filename}  — serve screenshot PNG/JPEG
    GET /files/videos/{filename}       — serve video recording (WebM/MP4)
    GET /files/logs/{filename}         — serve log text files
    GET /files/reports/{filename}      — serve report HTML/JSON files

Security:
    - Path traversal prevention via os.path.basename
    - 404 if file does not exist
    - Filenames validated against allowed characters
"""

import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="/files", tags=["files"])

# Base storage directory — matches volume mount in docker-compose.yml
STORAGE_BASE = Path(os.getenv("STORAGE_DIR", "/app/storage"))

SCREENSHOTS_DIR = STORAGE_BASE / "screenshots"
VIDEOS_DIR      = STORAGE_BASE / "videos"
LOGS_DIR        = STORAGE_BASE / "logs"
REPORTS_DIR     = STORAGE_BASE / "reports"

# Only allow safe filename characters (alphanumeric, hyphens, underscores, dots)
_SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+$")


def _safe_resolve(directory: Path, filename: str) -> Path:
    """
    Resolve a file path safely, preventing directory traversal attacks.

    Args:
        directory: The base directory the file must be inside.
        filename:  The requested filename (basename only).

    Returns:
        Absolute Path to the file.

    Raises:
        HTTPException 400: If the filename contains unsafe characters.
        HTTPException 404: If the resolved path is outside the directory
                           or the file does not exist.
    """
    # Strip any path components — only the basename is allowed
    safe_name = os.path.basename(filename)

    if not _SAFE_FILENAME_RE.match(safe_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename. Only alphanumeric characters, hyphens, underscores, and dots are allowed.",
        )

    resolved = (directory / safe_name).resolve()

    # Ensure the resolved path is still inside the intended directory
    if not str(resolved).startswith(str(directory.resolve())):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{safe_name}' not found.",
        )

    return resolved


# ──────────────────────────────────────────────────────────────────────────────
# Screenshots
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/screenshots/{filename}",
    summary="Download a test screenshot",
    response_description="Screenshot image file (PNG or JPEG)",
)
async def get_screenshot(filename: str) -> FileResponse:
    """
    Serve a screenshot captured during a test run.

    Supports PNG and JPEG files. Files are stored at the path configured
    by the SCREENSHOTS_DIR environment variable (default: /app/storage/screenshots).
    """
    path = _safe_resolve(SCREENSHOTS_DIR, filename)
    media_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=path.name,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Videos
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/videos/{filename}",
    summary="Download a test recording video",
    response_description="Video recording file (WebM or MP4)",
)
async def get_video(filename: str) -> FileResponse:
    """
    Serve a video recording of a Playwright test run.

    Playwright typically produces WebM recordings; MP4 is also supported.
    """
    path = _safe_resolve(VIDEOS_DIR, filename)

    if filename.lower().endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.lower().endswith(".webm"):
        media_type = "video/webm"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=path.name,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Logs
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/logs/{filename}",
    summary="Download a test execution log file",
    response_description="Plain-text or JSON log file",
)
async def get_log(filename: str) -> FileResponse:
    """
    Serve a log file produced during a test run or AI analysis step.
    """
    path = _safe_resolve(LOGS_DIR, filename)
    media_type = (
        "application/json"
        if filename.lower().endswith(".json")
        else "text/plain; charset=utf-8"
    )
    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=path.name,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────────────────────────────────────
@router.get(
    "/reports/{filename}",
    summary="Download a test report file",
    response_description="HTML or JSON report file",
)
async def get_report(filename: str) -> FileResponse:
    """
    Serve a generated test report file.

    Reports are typically HTML (Allure index) or JSON (machine-readable summary).
    For full Allure HTML reports, use the /allure route served by the Allure container.
    """
    path = _safe_resolve(REPORTS_DIR, filename)

    if filename.lower().endswith(".html"):
        media_type = "text/html; charset=utf-8"
    elif filename.lower().endswith(".json"):
        media_type = "application/json"
    elif filename.lower().endswith(".xml"):
        media_type = "application/xml"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=path.name,
    )
