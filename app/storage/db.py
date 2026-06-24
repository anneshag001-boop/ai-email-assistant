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
    _seed_first_user()
    from app.storage.repository import seed_default_containers
    db = SessionLocal()
    try:
        seed_default_containers(db)
    finally:
        db.close()


def _seed_first_user():
    db = SessionLocal()
    try:
        from app.storage.models import User
        from app.core.security import hash_password
        existing = db.query(User).count()
        if existing == 0:
            user = User(email="admin@localhost", password_hash=hash_password("admin123"))
            db.add(user)
            db.commit()
    finally:
        db.close()


def _migrate_existing_db():
    conn = engine.connect()
    inspector = inspect(conn)

    # users table is created by Base.metadata.create_all if not exists

    tables_to_check = {
        "email_records": ["is_sent", "in_reply_to_id", "user_id"],
        "email_accounts": ["imap_host", "imap_port", "imap_user", "imap_password", "imap_use_ssl", "gmail_token", "gmail_token_expiry", "user_id", "initial_sync_done", "last_sync_at"],
        "prediction_records": ["user_id"],
        "feedback_records": ["user_id"],
        "containers": ["user_id"],
        "audit_logs": ["user_id"],
    }

    for table, columns in tables_to_check.items():
        if not inspector.has_table(table):
            continue
        existing_cols = [c["name"] for c in inspector.get_columns(table)]
        for col in columns:
            if col not in existing_cols:
                col_type = "INTEGER REFERENCES users(id) DEFAULT 1" if col == "user_id" else None
                if col == "is_sent":
                    col_type = "BOOLEAN DEFAULT 0"
                elif col == "in_reply_to_id":
                    col_type = "INTEGER REFERENCES email_records(id)"
                elif col == "imap_host":
                    col_type = "VARCHAR(255) DEFAULT 'imap.gmail.com'"
                elif col == "imap_port":
                    col_type = "INTEGER DEFAULT 993"
                elif col == "imap_user":
                    col_type = "VARCHAR(255)"
                elif col == "imap_password":
                    col_type = "VARCHAR(255)"
                elif col == "imap_use_ssl":
                    col_type = "BOOLEAN DEFAULT 1"
                elif col == "gmail_token":
                    col_type = "TEXT"
                elif col == "gmail_token_expiry":
                    col_type = "DATETIME"
                elif col == "initial_sync_done":
                    col_type = "BOOLEAN DEFAULT 0"
                elif col == "last_sync_at":
                    col_type = "DATETIME"
                if col_type:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()

    # Remove unique constraint on containers.name since per-user names can repeat
    if inspector.has_table("containers"):
        # SQLite doesn't support DROP CONSTRAINT easily, so skip this migration
        pass

    # Create missing indexes (safe to run repeatedly — IF NOT EXISTS is idempotent)
    index_defs = [
        ("ix_email_record_dedup", "email_records", ["message_id", "provider", "user_id"]),
        ("ix_email_records_user_id", "email_records", ["user_id"]),
        ("ix_email_records_received_at", "email_records", ["received_at"]),
        ("ix_prediction_records_user_id", "prediction_records", ["user_id"]),
        ("ix_prediction_records_email_id", "prediction_records", ["email_id"]),
        ("ix_feedback_records_user_id", "feedback_records", ["user_id"]),
        ("ix_containers_user_id", "containers", ["user_id"]),
        ("ix_email_accounts_user_id", "email_accounts", ["user_id"]),
        ("ix_audit_logs_user_id", "audit_logs", ["user_id"]),
    ]
    for idx_name, table, columns in index_defs:
        try:
            cols = ", ".join(columns)
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})"))
            conn.commit()
        except Exception:
            pass  # table might not exist yet; metadata.create_all will handle new DBs

    conn.close()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
