# ACM LetterForge

AI-assisted official letters for ACM NMAMIT: the AI drafts the **subject and body only**; the letterhead, margins, fonts and signature positions come from your approved `.docx` template, so output matches a hand-prepared letter. Exports DOCX and PDF.

> **The Docker container is disposable. `/data` is the persistent application data.**

## Architecture
- **Frontend:** React + TypeScript + Tailwind (Vite), built into static files.
- **Backend:** FastAPI + SQLAlchemy + SQLite, python-docx/docxtpl for templates, LibreOffice for DOCX to PDF, Groq (Qwen) for text.
- **One container** serves the API and the built frontend on port 8000.
- **Persistent data** (`/data` in Docker): `letterforge.db` and `storage/{templates,signatures,generated}`. Nothing that must survive a deployment lives in the image.
- SQLite is intentionally used as a **single-instance** database: run one container, never several against the same `/data`.

## Environment variables
See `.env.example`. Key ones: `GROQ_API_KEY`, `GROQ_MODEL`, `APP_PASSWORD`, `DATABASE_URL`, `STORAGE_DIR`, `CORS_ORIGINS`, `MAX_UPLOAD_MB`. Never commit `.env`.

## Local development (no Docker)
```bash
# backend
cd backend && python -m venv venv && venv\Scripts\activate   # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env     # set GROQ_API_KEY, and use DATABASE_URL=sqlite:///./letterforge.db, STORAGE_DIR=./storage
uvicorn app.main:app --reload
# frontend (second terminal)
cd frontend && npm install --legacy-peer-deps && npm run dev      # http://localhost:5173
```
For exact PDFs locally, install LibreOffice (or have MS Word on Windows).

## Docker (production-like)
```bash
cp .env.example .env        # fill in GROQ_API_KEY and APP_PASSWORD; unset DATA_DIR to use a named volume
docker compose up --build   # http://localhost:8000   (health: /health)
```

## Production
Oracle Cloud Always Free + Caddy HTTPS: see **[DEPLOYMENT.md](DEPLOYMENT.md)** (setup, update workflow, backups, migration).

## Backups
`./scripts/backup.sh` writes a consistent `letterforge-<timestamp>.tar.gz` (database + storage). Copy backups off the VM regularly. Details and restore steps are in DEPLOYMENT.md.

## Templates
Official letterheads live in `backend/storage/templates/`. They are copied into an empty `/data/storage` on first start and never overwritten afterwards. Keep the `{{ ... }}` tags unbroken when editing a template in Word.
