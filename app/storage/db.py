from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from app.core.settings import settings
from app.storage.models import Base

engine = create_engine(
    settings.effective_database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.effective_database_url else {}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_existing_db()
    from app.storage.repository import seed_default_containers
    db = SessionLocal()
    try:
        seed_default_containers(db)
    finally:
        db.close()


def _migrate_existing_db():
    conn = engine.connect()
    inspector = inspect(conn)
    er_cols = [c["name"] for c in inspector.get_columns("email_records")]
    if "is_sent" not in er_cols:
        conn.execute(text("ALTER TABLE email_records ADD COLUMN is_sent BOOLEAN DEFAULT 0"))
        conn.commit()
    if "in_reply_to_id" not in er_cols:
        conn.execute(text("ALTER TABLE email_records ADD COLUMN in_reply_to_id INTEGER REFERENCES email_records(id)"))
        conn.commit()

    ea_cols = [c["name"] for c in inspector.get_columns("email_accounts")]
    if "imap_host" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN imap_host VARCHAR(255) DEFAULT 'imap.gmail.com'"))
        conn.commit()
    if "imap_port" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN imap_port INTEGER DEFAULT 993"))
        conn.commit()
    if "imap_user" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN imap_user VARCHAR(255)"))
        conn.commit()
    if "imap_password" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN imap_password VARCHAR(255)"))
        conn.commit()
    if "imap_use_ssl" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN imap_use_ssl BOOLEAN DEFAULT 1"))
        conn.commit()
    if "gmail_token" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN gmail_token TEXT"))
        conn.commit()
    if "gmail_token_expiry" not in ea_cols:
        conn.execute(text("ALTER TABLE email_accounts ADD COLUMN gmail_token_expiry DATETIME"))
        conn.commit()
    conn.close()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
