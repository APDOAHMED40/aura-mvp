from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "AI Executive Agent"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    google_gemini_api_key: str = ""

    database_url: str = "sqlite+aiosqlite:///./data/agent.db"

    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = base_dir / "data"
    logs_dir: Path = base_dir / "logs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
