# ============================================================
# Personal AI Presentation — Backend Production Dockerfile
# FastAPI + Uvicorn multi-worker + APScheduler graceful shutdown
# ============================================================

FROM python:3.12-slim

LABEL org.opencontainers.image.title="Personal AI Presentation - Backend"
LABEL org.opencontainers.image.description="FastAPI backend for AI presentation generation"

# ── 系统依赖 ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── 工作目录 ──
WORKDIR /app

# ── Python 依赖 (分层缓存) ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 源码 ──
COPY app/ ./app/

# ── 非 root 运行 ──
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# ── 健康检查 ──
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── 多 Worker 启动 + 安全停机 ──
# 2 workers = 适合 1-2 CPU 核心的云实例
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --timeout-keep-alive 30"]
