from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    database_url: str = "sqlite:///./letterforge.db"  # swap for postgresql+psycopg://...
    storage_dir: str = "./storage"
    app_password: str = ""  # set to require a password (HTTP Basic) - use this when hosting online
    class Config:
        env_file = ".env"

settings = Settings()
