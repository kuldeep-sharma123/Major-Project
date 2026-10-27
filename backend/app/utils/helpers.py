"""
General-purpose helper utilities for the AI Autonomous Testing Agent.
"""
from __future__ import annotations

import asyncio
import math
import re
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine, Iterable, List, TypeVar
from urllib.parse import urlparse

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.logger import logger

T = TypeVar("T")


# ── Identity helpers ───────────────────────────────────────────────────────

def generate_uuid() -> uuid.UUID:
    """Return a random UUID4."""
    return uuid.uuid4()


def generate_uuid_str() -> str:
    """Return a random UUID4 as hyphenated lowercase string."""
    return str(uuid.uuid4())


# ── URL helpers ────────────────────────────────────────────────────────────

def sanitize_url(url: str) -> str:
    """Normalise a URL: strip trailing slash, ensure scheme."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def extract_domain(url: str) -> str:
    """Return the netloc (domain) portion of a URL."""
    parsed = urlparse(url)
    return parsed.netloc or url


def is_same_domain(base_url: str, link_url: str) -> bool:
    """Check whether *link_url* belongs to the same domain as *base_url*."""
    return extract_domain(base_url) == extract_domain(link_url)


# ── File helpers ───────────────────────────────────────────────────────────

_UNSAFE_CHARS = re.compile(r"[^\w\-.]")


def safe_filename(name: str, extension: str = "") -> str:
    """
    Sanitise *name* into a filesystem-safe filename.

    Examples:
        safe_filename("My Test Case (login)", ".py") -> "My_Test_Case_login_.py"
    """
    sanitized = _UNSAFE_CHARS.sub("_", name).strip("_")
    if extension and not extension.startswith("."):
        extension = "." + extension
    return sanitized + extension


def ensure_dir(path: str | Path) -> Path:
    """Create directory (and parents) if it does not exist; return Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ── Duration / time helpers ────────────────────────────────────────────────

def format_duration(seconds: float) -> str:
    """
    Convert *seconds* (float) to a human-readable string.

    Examples:
        1.234  -> "1.23s"
        65.0   -> "1m 05s"
        3661.0 -> "1h 01m 01s"
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m {secs:02d}s"


# ── Collection helpers ─────────────────────────────────────────────────────

def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    """
    Split *lst* into sub-lists of at most *size* elements.

    Example:
        chunk_list([1,2,3,4,5], 2) -> [[1,2],[3,4],[5]]
    """
    if size <= 0:
        raise ValueError("Chunk size must be positive")
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def flatten(nested: Iterable[Iterable[T]]) -> List[T]:
    """Flatten one level of nesting."""
    return [item for sublist in nested for item in sublist]


# ── Async retry ────────────────────────────────────────────────────────────

async def retry_async(
    coro_fn: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exceptions: tuple = (Exception,),
    **kwargs: Any,
) -> T:
    """
    Execute *coro_fn* with exponential-backoff retry.

    Args:
        coro_fn:      Async callable to retry.
        *args:        Positional arguments forwarded to *coro_fn*.
        max_attempts: Maximum number of attempts (default 3).
        wait_min:     Minimum wait between retries in seconds.
        wait_max:     Maximum wait between retries in seconds.
        exceptions:   Tuple of exception types that trigger a retry.
        **kwargs:     Keyword arguments forwarded to *coro_fn*.

    Returns:
        The return value of *coro_fn* on success.

    Raises:
        The last exception raised after all attempts are exhausted.
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    ):
        with attempt:
            logger.debug(
                f"retry_async attempt {attempt.retry_state.attempt_number}/{max_attempts} "
                f"for {coro_fn.__name__}"
            )
            return await coro_fn(*args, **kwargs)


# ── String helpers ─────────────────────────────────────────────────────────

def truncate(text: str, max_len: int = 200, suffix: str = "…") -> str:
    """Truncate *text* to *max_len* characters, appending *suffix* if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


# ── Windows Proactor / Subprocess Execution Runner ─────────────────────────

async def run_coro_with_proactor(coro_fn: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any) -> T:
    """
    Executes an async Playwright coroutine safely on Windows.
    Guarantees a ProactorEventLoop is used so that Playwright browser subprocesses
    do not fail with NotImplementedError under Uvicorn's SelectorEventLoop.
    """
    import sys
    loop = asyncio.get_running_loop()
    is_selector = sys.platform == "win32" and "Selector" in type(loop).__name__
    if not is_selector:
        try:
            return await coro_fn(*args, **kwargs)
        except NotImplementedError:
            pass

    def _worker():
        proactor_loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(proactor_loop)
        try:
            return proactor_loop.run_until_complete(coro_fn(*args, **kwargs))
        finally:
            proactor_loop.close()

    return await asyncio.to_thread(_worker)

