from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

_url = make_url(settings.database_url)
_sqlite = _url.get_backend_name() == "sqlite"
if _sqlite and _url.database and _url.database != ":memory:":
    Path(_url.database).parent.mkdir(parents=True, exist_ok=True)  # empty /data volume on first start is fine

# SQLite: allow use from FastAPI's worker threads and wait (15 s) instead of failing if the file is briefly locked.
args = {"check_same_thread": False, "timeout": 15} if _sqlite else {}
engine = create_engine(settings.database_url, connect_args=args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase): pass

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
