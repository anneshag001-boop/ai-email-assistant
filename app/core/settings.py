from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Email Assistant"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    encryption_key: str = "change-me-in-production"

    database_url: str = "sqlite:///./data/email_assistant.db"

    imap_poll_interval: int = 300
    spam_threshold: float = 0.7
    confidence_threshold: float = 0.6
    spam_retention_days: int = 30
    dashboard_refresh_interval: int = 60

    ollama_enabled: bool = True
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 30

    groq_api_key: Optional[str] = None
    groq_model: str = "llama3-8b"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_default_sender: Optional[str] = None

    @property
    def effective_database_url(self) -> str:
        return self.database_url

    class Config:
        env_file = ".env"


settings = Settings()
