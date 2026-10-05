# LetterForge (backend core)
Run: `cp .env.example .env`, add GROQ_API_KEY, then `docker compose up` (or `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`).
Docs: http://localhost:8000/docs. Four placeholder letterheads are seeded on startup.
Real letterheads: upload a .docx via POST /api/templates; keep the letterhead in the Word header and use the tags {{ sender }}, {{ through_block }}, {{ recipient }}, {{ subject }}, {{ body }} and the signatories loop (see docs.py).
Postgres: set DATABASE_URL to a postgresql+psycopg URL, add the driver, run Alembic (`alembic init`, point env.py at app.models).
