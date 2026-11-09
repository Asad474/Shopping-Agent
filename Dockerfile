# ==============================================================================
# Stage 1: Build virtual environment with uv
# ==============================================================================
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.14-slim AS builder

# Copy uv binaries from official Astral image
COPY --from=uv_bin /uv /uvx /bin/

# Optimize uv performance & caching
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# ---------------------------------------------------------------------------
# 1. Install dependencies first (cache-friendly: changes to src/ don't bust this)
# ---------------------------------------------------------------------------
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ---------------------------------------------------------------------------
# 2. Copy source and install the project
# ---------------------------------------------------------------------------
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------------------------------------------------------------------------
# 3. Trim bloat from the venv
#    - Drop __pycache__, .pyc, tests, and docs
#    - Drop Streamlit / LangChain extras that this app does NOT use
# ---------------------------------------------------------------------------
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type d \( -name "tests" -o -name "test" \) -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /app/.venv/lib/python*/site-packages/*/docs 2>/dev/null || true && \
    /app/.venv/bin/python -m pip uninstall -y \
    pydeck \
    pillow \
    altair \
    langsmith \
    2>/dev/null || true

# ==============================================================================
# Stage 2: Minimal Runtime
# ==============================================================================
FROM python:3.14-slim AS runner

# Create a non-root system user for security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Configure Python and Streamlit runtime environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Copy only the compiled virtualenv from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application files
COPY --chown=appuser:appuser src /app/src
COPY --chown=appuser:appuser app.py /app/app.py
COPY --chown=appuser:appuser setup_db.py /app/setup_db.py
COPY --chown=appuser:appuser store.db /app/store.db

# Ensure /app and upload dir are writable by appuser (SQLite journal/lock files)
RUN mkdir -p /app/resources && chown -R appuser:appuser /app

USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Lightweight health check using Python standard library (no curl required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Start Streamlit application
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]