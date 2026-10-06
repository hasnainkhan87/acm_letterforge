# syntax=docker/dockerfile:1
# --- Stage 1: build the React/Vite frontend ---------------------------------
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund
COPY frontend/ .
RUN npm run build

# --- Stage 2: FastAPI + LibreOffice. Image = code + dependencies ONLY --------
# All persistent data lives in /data, which is mounted at runtime (never baked in).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 \
    HOME=/home/app \
    DATABASE_URL=sqlite:////data/letterforge.db \
    STORAGE_DIR=/data/storage

# LibreOffice Writer for DOCX->PDF; Carlito is metric-compatible with Calibri, Liberation with Arial/Times.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libreoffice-writer fonts-liberation fonts-crosextra-carlito \
 && rm -rf /var/lib/apt/lists/*

# Non-root runtime user (uid 1000 matches the default Ubuntu user, which keeps host bind mounts easy).
RUN useradd --uid 1000 --create-home --home-dir /home/app app \
 && mkdir -p /data/storage && chown -R app:app /data

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY --chown=app:app backend/ ./
COPY --from=web --chown=app:app /web/dist ./static

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

# One process, exec form: uvicorn is PID 1 and shuts down cleanly on SIGTERM. Single instance only (SQLite).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
