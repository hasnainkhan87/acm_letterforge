from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Every deployment-sensitive value comes from the environment (see .env.example)."""
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    database_url: str = "sqlite:///./letterforge.db"      # Docker: sqlite:////data/letterforge.db
    storage_dir: str = "./storage"                         # Docker: /data/storage
    app_password: str = ""                                 # empty = no password (local dev only)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"  # comma-separated; same-origin prod needs none
    max_upload_mb: int = 10

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip() and o.strip() != "*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
