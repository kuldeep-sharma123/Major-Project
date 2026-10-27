# ============================================================
# Stage 1: Builder — install dependencies in isolated layer
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build deps needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer cache
COPY requirements.txt .

# Install Python dependencies into a prefix directory
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2: Runtime — slim image, no build tools
# ============================================================
FROM python:3.11-slim AS runtime

# Labels for image metadata
LABEL maintainer="AI Testing Agent Team" \
      version="1.0.0" \
      description="AI Autonomous Testing Agent – FastAPI Backend"

WORKDIR /app

# Install only runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    # Playwright system deps for headless browser automation
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libexpat1 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Create directories for file storage with proper ownership
RUN mkdir -p /app/storage/screenshots \
             /app/storage/videos \
             /app/storage/logs \
             /app/storage/reports && \
    chown -R appuser:appgroup /app

# Copy application source code
COPY --chown=appuser:appgroup . .

# Install Playwright browsers as root before switching user
# Chromium is sufficient; skip Firefox/WebKit to reduce image size
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium && \
    chown -R appuser:appgroup /root/.cache 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check — polls the /health endpoint every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use uvicorn with multiple workers for production
# Workers = (2 * CPU cores) + 1 is the standard formula; using 4 here
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools"]
