# Single-service build for hosting: React app is built and served by FastAPI; LibreOffice gives exact PDFs.
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend .
RUN npm run build

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer fonts-liberation fonts-crosextra-carlito \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend .
COPY --from=web /web/dist ./static
ENV STORAGE_DIR=/data/storage DATABASE_URL=sqlite:////data/letterforge.db
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
