from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Email Assistant"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    encryption_key: str = "change-me-in-production"

    database_url: str = "sqlite:///./data/email_assistant.db"

    use_postgres: bool = False
    postgres_user: str = "email_assistant"
    postgres_password: str = "changeme"
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "email_assistant"

    # Gmail OAuth2
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_redirect_uri: Optional[str] = None

    # Outlook / Microsoft Graph OAuth2
    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None
    outlook_redirect_uri: Optional[str] = None
    outlook_tenant: str = "common"

    imap_poll_interval: int = 300

    spam_model_path: str = "data/models/spam_model.pkl"
    classifier_model_path: str = "data/models/classifier_model.pkl"
    vectorizer_path: str = "data/models/vectorizer.pkl"

    spam_threshold: float = 0.7
    confidence_threshold: float = 0.6
    spam_retention_days: int = 30
    dashboard_refresh_interval: int = 60

    # SpamAssassin
    spamassassin_enabled: bool = False
    spamassassin_host: str = "spamassassin"
    spamassassin_port: int = 783

    # Ollama SLM
    ollama_enabled: bool = True
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 30

    # SMTP for sending emails
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_default_sender: Optional[str] = None

    @property
    def effective_database_url(self) -> str:
        if self.use_postgres:
            return (f"postgresql://{self.postgres_user}:{self.postgres_password}"
                    f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}")
        return self.database_url

    class Config:
        env_file = ".env"


settings = Settings()
