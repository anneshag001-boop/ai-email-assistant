# AI Email Assistant — Full Project Analysis

> Generated: 2026-06-14 | Python ≥3.11 | FastAPI | SQLAlchemy | scikit-learn | Docker

---

## 1. Project Overview

**AI Email Assistant** is an intelligent email classification and routing system that ingests emails from multiple providers (Gmail, Outlook, IMAP), classifies them using ML (scikit-learn / optional Hugging Face transformers), detects spam (rule-based / SpamAssassin), and routes them to appropriate folders based on configurable rules. It includes a feedback loop for continuous retraining, a glassmorphic dashboard, scheduled jobs, OAuth2 authentication, and Docker-based deployment.

**Purpose**: Automate email triage — sort, prioritize, and route emails with minimal human intervention.

**Min Python Version**: 3.11

---

## 2. Complete File Tree

```
D:\ai-email-assistant\
│
├── .env                                # Active environment variables (dev)
├── .env.example                        # Template with all configurable vars
├── pyproject.toml                      # Project metadata, deps, pytest config
├── requirements.txt                    # Pinned dependencies
├── README.md                           # Quick-start & API docs
├── run.py                              # Entry point: uvicorn --reload :8000
│
├── app\                                # ─── Application Package ───
│   ├── __init__.py                     # (empty)
│   ├── main.py                         # FastAPI app factory, router mount, /dashboard
│   ├── config.py                       # Legacy config (dotenv) — superseded by core/settings.py
│   ├── schemas.py                      # Legacy Pydantic schemas (ingest, classify, feedback)
│   │
│   ├── ai\                             # AI/ML Pipeline
│   │   ├── __init__.py
│   │   ├── classifier.py               # EmailClassifier — unified ML/HF/rule fallback
│   │   ├── hf_classifier.py            # HFEmailClassifier — Hugging Face pipeline
│   │   ├── model_loader.py             # ModelLoader — pickle save/load
│   │   ├── scorer.py                   # compute_priority_score(), compute_confidence()
│   │   ├── spam_detector.py            # SpamDetector — SpamAssassin + rule-based
│   │   └── spamassassin_client.py      # SpamAssassinClient — raw SPAMD socket protocol
│   │
│   ├── api\                            # REST API Layer
│   │   ├── __init__.py
│   │   ├── routes.py                   # 11 core API endpoints
│   │   ├── auth_routes.py              # OAuth2 login/callback for Gmail & Outlook
│   │   └── schemas.py                  # Pydantic request/response models
│   │
│   ├── core\                           # Core Infrastructure
│   │   ├── __init__.py
│   │   ├── settings.py                 # Settings class (Pydantic Settings) — 30 fields
│   │   ├── auth.py                     # OAuth2 flows, Fernet+PBKDF2 token encryption
│   │   └── logger.py                   # Structured logging setup
│   │
│   ├── feedback\                       # User Feedback & Retraining
│   │   ├── __init__.py
│   │   ├── capture.py                  # capture_feedback() — saves + audits
│   │   └── retrain.py                  # retrain_classifier() — LogisticRegression + TF-IDF
│   │
│   ├── ingestion\                      # Email Source Clients
│   │   ├── __init__.py                 # NormalizedEmail dataclass
│   │   ├── gmail_client.py            # GmailClient — Gmail API v1
│   │   ├── imap_client.py             # IMAPClient — generic IMAP SSL
│   │   └── outlook_client.py          # OutlookClient — Microsoft Graph API
│   │
│   ├── jobs\                           # Scheduled Jobs (APScheduler)
│   │   ├── __init__.py
│   │   ├── cleanup.py                  # cleanup_spam() — deletes spam >30 days
│   │   ├── retrain_job.py             # scheduled_retrain() — triggers retrain
│   │   └── sync_job.py                # sync_imap() — full pipeline: fetch→parse→clean→classify→route→store
│   │
│   ├── monitoring\                     # Metrics & Monitoring
│   │   ├── __init__.py
│   │   └── metrics.py                  # get_metrics() — dashboard queries
│   │
│   ├── preprocessing\                  # Text Preprocessing
│   │   ├── __init__.py
│   │   ├── cleaner.py                  # HTML strip, signature removal, quote removal
│   │   ├── dedupe.py                   # SHA-256 content deduplication
│   │   └── parser.py                   # Email address parsing, domain extraction
│   │
│   ├── routing\                        # Routing Engine
│   │   ├── __init__.py
│   │   ├── router.py                   # route_email() — decision logic
│   │   ├── actions.py                  # EmailActions — folder/action mapping
│   │   └── rules.py                    # RoutingRule, FOLDER_MAP, DEFAULT_RULES
│   │
│   ├── storage\                        # Database Layer
│   │   ├── __init__.py
│   │   ├── db.py                       # SQLAlchemy engine, SessionLocal, get_db()
│   │   ├── models.py                   # ORM: EmailRecord, PredictionRecord, FeedbackRecord, AuditLog
│   │   └── repository.py              # Repositories: Email, Prediction, Feedback, AuditLog
│   │
│   ├── templates\                      # Frontend Templates
│   │   └── dashboard.html             # Glassmorphic dashboard (726 lines, Jinja2)
│   │
│   └── utils\                          # Utilities
│       ├── __init__.py
│       ├── email_utils.py             # Regex extraction, unsubscribe detection, provider detection
│       └── text_utils.py              # Language detection, word count, URL stripping
│
├── data\                               # ─── Data & Models ───
│   ├── email_assistant.db             # SQLite database (24 KB)
│   ├── models\
│   │   ├── classifier_model.pkl       # Serialized LogisticRegression (6.7 KB)
│   │   ├── vectorizer.pkl             # Serialized TF-IDF vectorizer (5.5 KB)
│   │   └── models.py                  # Legacy/alternate ORM models
│   ├── processed\                     # (empty)
│   ├── raw\                           # (empty)
│   └── training\                      # (empty)
│
├── deploy\                             # ─── Deployment ───
│   ├── docker-compose.yml             # 3 services: app, db (PostgreSQL), spamassassin
│   ├── Dockerfile                     # Python 3.11-slim image
│   └── nginx.conf                     # Reverse proxy :80 → app :8000
│
├── scripts\                            # ─── Utility Scripts ───
│   ├── train_model.py                 # Initial model training (6 categories, 27 samples)
│   ├── evaluate_model.py             # Model evaluation (10 samples, classification report)
│   └── seed_labels.py                # DB initialization + audit log seeding
│
└── tests\                              # ─── Test Suite ───
    ├── __init__.py
    ├── conftest.py                    # Adds project root to sys.path
    ├── test_classifier.py             # 10 tests: categories, priority, confidence
    ├── test_cleanup.py                # 2 tests: retention setting, cleanup execution
    ├── test_hf_classifier.py          # 3 tests: init, fallback, integration
    ├── test_ingestion.py              # 8 tests: NormalizedEmail, parsing, cleaning
    ├── test_router.py                 # 9 tests: spam, low-conf, categories
    ├── test_spam_detector.py          # 6 tests: spam detection, rules, sender impact
    └── test_spamassassin.py           # 5 tests: client, parsing, connection fallback
```

---

## 3. Tech Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | ≥3.11 | Primary language |
| **Web Framework** | FastAPI | 0.136+ | ASGI REST API |
| **ASGI Server** | Uvicorn | 0.49+ | App server |
| **Template Engine** | Jinja2 | 3.1+ | Dashboard rendering |
| **Validation** | Pydantic | 2.13+ | Data & settings validation |
| **Config** | Pydantic Settings | 2.14+ | Environment config management |
| **ORM** | SQLAlchemy | 2.0+ | Database ORM |
| **DB (Dev)** | SQLite | Built-in | Local development |
| **DB (Prod)** | PostgreSQL | 15-alpine | Production database |
| **DB Adapter** | psycopg2-binary | 2.9+ | PostgreSQL driver |
| **ML Classifier** | scikit-learn | 1.9+ | LogisticRegression + TfidfVectorizer |
| **DL (Optional)** | transformers + torch | ≥4.44 / ≥2.4 | Hugging Face classifier |
| **Numerical** | NumPy + SciPy | 2.4+ / 1.17+ | ML backend |
| **Serialization** | joblib / pickle | 1.5+ | Model persistence |
| **Gmail Client** | google-api-python-client | 2.147+ | Gmail API v1 |
| **Gmail Auth** | google-auth-oauthlib | 1.2+ | Gmail OAuth2 |
| **IMAP Client** | IMAPClient | 3.1+ | Generic IMAP |
| **Outlook Client** | requests | 2.34+ | Microsoft Graph API |
| **HTML Parsing** | BeautifulSoup4 | 4.15+ | HTML→text conversion |
| **Token Encrypt** | cryptography | 49+ | Fernet + PBKDF2 encryption |
| **Scheduler** | APScheduler | 3.11+ | Job scheduling |
| **Timezone** | tzlocal + tzdata | 5.3+ / 2026+ | Timezone support |
| **Testing** | pytest | 9.0+ | Test runner |
| **HTTP Test** | httpx | 0.27+ | HTTP test client |
| **Container** | Docker + Compose | — | Deployment |
| **Proxy** | Nginx | — | Reverse proxy |
| **Spam Filter** | SpamAssassin | latest (Docker) | External spam scoring |

### Not Yet Installed (optional dependencies)
| Package | Version Required | Purpose |
|---------|-----------------|---------|
| `transformers` | ≥4.44.0 | Hugging Face transformer models |
| `torch` | ≥2.4.0 | PyTorch backend for HF |
| `langdetect` | ≥1.0.9 | Language detection |
| `google-api-python-client` | ≥2.147.0 | Gmail API |
| `google-auth-oauthlib` | ≥1.2.0 | Gmail OAuth2 |
| `python-multipart` | ≥0.0.12 | Form data parsing |
| `httpx` | ≥0.27.2 | HTTP test client |

---

## 4. Configuration & Environment Variables

### Source: `app/core/settings.py` (Pydantic Settings — loaded from `.env`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `app_name` | `str` | `"AI Email Assistant"` | Application name |
| `debug` | `bool` | `False` | Debug mode |
| `secret_key` | `str` | `"change-me-in-production"` | Secret key for signing |
| `encryption_key` | `str` | `"change-me-in-production"` | Key for token encryption |
| `database_url` | `str` | `"sqlite:///./data/email_assistant.db"` | Database URL |
| `use_postgres` | `bool` | `False` | Toggle PostgreSQL |
| `postgres_user` | `str` | `"email_assistant"` | PostgreSQL user |
| `postgres_password` | `str` | `"changeme"` | PostgreSQL password |
| `postgres_host` | `str` | `"db"` | PostgreSQL host |
| `postgres_port` | `int` | `5432` | PostgreSQL port |
| `postgres_db` | `str` | `"email_assistant"` | PostgreSQL database name |
| `gmail_client_id` | `Optional[str]` | `None` | Gmail OAuth2 client ID |
| `gmail_client_secret` | `Optional[str]` | `None` | Gmail OAuth2 client secret |
| `gmail_redirect_uri` | `Optional[str]` | `None` | Gmail OAuth2 redirect URI |
| `outlook_client_id` | `Optional[str]` | `None` | Outlook OAuth2 client ID |
| `outlook_client_secret` | `Optional[str]` | `None` | Outlook OAuth2 client secret |
| `outlook_redirect_uri` | `Optional[str]` | `None` | Outlook OAuth2 redirect URI |
| `outlook_tenant` | `str` | `"common"` | Outlook tenant |
| `imap_poll_interval` | `int` | `300` | IMAP polling interval (seconds) |
| `spam_model_path` | `str` | `"data/models/spam_model.pkl"` | Spam model path |
| `classifier_model_path` | `str` | `"data/models/classifier_model.pkl"` | Classifier model path |
| `vectorizer_path` | `str` | `"data/models/vectorizer.pkl"` | Vectorizer path |
| `spam_threshold` | `float` | `0.7` | Spam score threshold (0-1) |
| `confidence_threshold` | `float` | `0.6` | Minimum confidence for auto-routing |
| `spam_retention_days` | `int` | `30` | Days before auto-deleting spam |
| `dashboard_refresh_interval` | `int` | `60` | Dashboard auto-refresh (seconds) |
| `spamassassin_enabled` | `bool` | `False` | Enable SpamAssassin |
| `spamassassin_host` | `str` | `"spamassassin"` | SpamAssassin host |
| `spamassassin_port` | `int` | `783` | SpamAssassin port |
| `hf_enabled` | `bool` | `False` | Enable Hugging Face transformer |
| `hf_model_name` | `str` | `"cross-encoder/ms-marco-MiniLM-L-6-v2"` | HF model name |

**Property**: `effective_database_url` — returns PostgreSQL URL if `use_postgres=True`, else `database_url`.

### Source: `app/config.py` (Legacy — partially redundant)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `"ai-email-assistant"` | App name |
| `DATABASE_URL` | `"sqlite:///./email_assistant.db"` | Database URL |
| `IMAP_HOST` | `"imap.gmail.com"` | IMAP server |
| `IMAP_PORT` | `993` | IMAP port |
| `IMAP_USER` | `""` | IMAP user |
| `IMAP_PASSWORD` | `""` | IMAP password |
| `IMAP_INBOX` | `"INBOX"` | IMAP folder |
| `SPAM_THRESHOLD` | `5.0` | Spam threshold (legacy) |
| `LOW_CONFIDENCE_THRESHOLD` | `0.60` | Low confidence threshold |
| `AUTO_DELETE_DAYS` | `30` | Auto-delete days |

### Current `.env` (Dev)
```
APP_NAME=AI Email Assistant
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=dev-encryption-key-change-in-production
DATABASE_URL=sqlite:///./data/email_assistant.db
USE_POSTGRES=false
SPAMASSASSIN_ENABLED=false
HF_ENABLED=false
SPAM_THRESHOLD=0.7
CONFIDENCE_THRESHOLD=0.6
SPAM_RETENTION_DAYS=30
```

---

## 5. Architecture & Data Flow

```
                         ┌─────────────────────────────────────┐
                         │          Email Sources              │
                         │  Gmail API │ Outlook Graph │ IMAP   │
                         └───────────────┬─────────────────────┘
                                         │
                         ┌───────────────▼─────────────────────┐
                         │        Ingestion Clients            │
                         │  GmailClient / OutlookClient /      │
                         │  IMAPClient                         │
                         │  Output: NormalizedEmail DTO        │
                         └───────────────┬─────────────────────┘
                                         │
                         ┌───────────────▼─────────────────────┐
                         │        Preprocessing                │
                         │  parser.py → cleaner.py → dedupe.py │
                         │  (addresses → strip HTML/sig/quote  │
                         │   → SHA-256 dedup)                  │
                         └───────────────┬─────────────────────┘
                                         │
              ┌──────────────────────────▼──────────────────────────┐
              │                 AI Pipeline                         │
              │  ┌─────────────────┐   ┌─────────────────────────┐  │
              │  │  SpamDetector   │   │   EmailClassifier       │  │
              │  │  (SpamAssassin  │   │   (scikit-learn         │  │
              │  │   or Rule-based)│   │    or HuggingFace       │  │
              │  │                 │   │    or Rule-based)       │  │
              │  └────────┬────────┘   └─────────────┬───────────┘  │
              │           │                          │              │
              │  ┌────────▼──────────────────────────▼───────────┐  │
              │  │              Scorer                           │  │
              │  │  compute_priority_score()                     │  │
              │  │  compute_confidence()                         │  │
              │  └────────┬──────────────────────────┬───────────┘  │
              └───────────┼──────────────────────────┼──────────────┘
                          │                          │
              ┌───────────▼──────────────────────────▼──────────────┐
              │                  Router (router.py)                 │
              │  spam → Trash/Spam                                  │
              │  low confidence → Review Queue                      │
              │  business → Business folder                         │
              │  private → Private folder                           │
              │  important → Important folder                       │
              │  other_work → archive                               │
              │  others → archive                                   │
              └───────────────────────┬─────────────────────────────┘
                                      │
              ┌───────────────────────▼─────────────────────────────┐
              │               Storage Layer                         │
              │  SQLite (dev) / PostgreSQL (prod)                   │
              │  Tables:                                            │
              │  ─ email_records      (id, message_id, sender,      │
              │  │                      recipients, subject,        │
              │  │                      body_text, body_html, ...)  │
              │  ─ prediction_records (id, email_id FK, spam_score, │
              │  │                      category_label,             │
              │  │                      routed_folder, ...)         │
              │  ─ feedback_records   (id, email_id FK, old_label,  │
              │  │                      corrected_label, ...)       │
              │  ─ audit_logs         (id, email_id FK, event_type, │
              │                        event_payload JSON, ...)     │
              └───────────────────────┬─────────────────────────────┘
                                      │
              ┌───────────────────────▼─────────────────────────────┐
              │      Monitoring & User Feedback                     │
              │  Dashboard (Jinja2+CSS glassmorphism)               │
              │  Metrics API (totals, rates, distributions)         │
              │  Feedback capture → retrain_classifier()            │
              └───────────────────────┬─────────────────────────────┘
                                      │
              ┌───────────────────────▼─────────────────────────────┐
              │         Scheduled Jobs (APScheduler)                │
              │  sync_job.py    → fetch→classify→route (IMAP poll)  │
              │  cleanup.py     → delete spam >30 days              │
              │  retrain_job.py → trigger model retrain             │
              └─────────────────────────────────────────────────────┘
```

---

## 6. Stack-by-Stack Deep Dives

---

### 6.1 Backend (FastAPI)

**Files**:
- `app/main.py` — FastAPI app factory, mounts `api/router`, `api/auth_routes`, serves `/dashboard`
- `app/api/routes.py` — 11 core endpoints
- `app/api/auth_routes.py` — OAuth2 login/callback (Gmail + Outlook)
- `app/api/schemas.py` — Pydantic request/response models

**Key classes in `app/api/schemas.py`**:
- `IngestEmailRequest` — sender, recipients, subject, body, provider, etc.
- `ClassifyRequest` — text body for classification
- `ClassifyResponse` — spam_score, is_spam, category_label, category_confidence, priority_score, routed_folder, routed_action
- `RouteResponse` — same as ClassifyResponse + ingested + email_id
- `FeedbackRequest` — email_id, corrected_label, note
- `EmailListResponse` — paginated email list
- `EmailDetailResponse` — single email with predictions
- `MetricsResponse` — dashboard statistics

**API Endpoints**:

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/dashboard` | — | HTML dashboard (Jinja2) |
| GET | `/docs` | — | Swagger UI (automatic) |
| POST | `/api/ingest/email` | `ingest_email()` | Ingest an email (parse+clean+dedup+store) |
| POST | `/api/classify/email` | `classify_email()` | Classify + score + route + store |
| POST | `/api/route/email` | `classify_email()` | Alias for classify |
| GET | `/api/emails` | `list_emails()` | List emails (paginated) |
| GET | `/api/emails/{id}` | `get_email()` | Single email with predictions |
| POST | `/api/feedback` | `submit_feedback()` | Submit correction feedback |
| GET | `/api/metrics` | `get_metrics()` | Dashboard metrics |
| POST | `/api/retrain` | `trigger_retrain()` | Trigger model retraining |
| POST | `/api/cleanup/spam` | `trigger_cleanup()` | Delete old spam |
| GET | `/auth/gmail/login` | `gmail_login()` | Gmail OAuth2 login |
| GET | `/auth/gmail/callback` | `gmail_callback()` | Gmail OAuth2 callback |
| GET | `/auth/outlook/login` | `outlook_login()` | Outlook OAuth2 login |
| GET | `/auth/outlook/callback` | `outlook_callback()` | Outlook OAuth2 callback |

**Dependency Injection**: `get_db()` provides `Session` to all endpoints.

---

### 6.2 AI/ML Pipeline

**Files**: `app/ai/classifier.py`, `hf_classifier.py`, `spam_detector.py`, `spamassassin_client.py`, `scorer.py`, `model_loader.py`

**EmailClassifier** (`app/ai/classifier.py`):
- Class-level cached instances: `_cached_model`, `_cached_vectorizer`, `_cached_hf`
- `classify(text: str)` returns `(category_label: str, confidence: float)`
- Strategy: HF enabled → `HFEmailClassifier`, else scikit-learn model loaded, else rule-based fallback
- Rule-based uses keyword matching on subject+body for 6 categories
- `reset_cache()` classmethod to clear cached models

**HFEmailClassifier** (`app/ai/hf_classifier.py`):
- `HFEmailClassifier(model_name: str)` — loads Hugging Face pipeline
- `classify(text: str)` — returns `(label: str, confidence: float)`
- Falls back to `"others"` with 0.5 confidence on failure

**SpamDetector** (`app/ai/spam_detector.py`):
- `SpamAssassinSpamDetector` — uses SpamAssassinClient if enabled
- `RuleBasedSpamDetector` — keyword rules + sender reputation + link ratio
- `SpamDetector` — unified wrapper: SA first, fallback to rule-based
- `SPAM_KEYWORDS` list: "buy now", "click here", "free", "limited offer", etc.
- `detect(text: str, sender: str)` returns `(is_spam: bool, spam_score: float)`

**SpamAssassinClient** (`app/ai/spamassassin_client.py`):
- Raw TCP socket client on port 783 (SPAMD protocol)
- `check_spam(text: str)` → `(is_spam: bool, score: float)`
- Sends `SYMBOLS` command, parses response

**Scorer** (`app/ai/scorer.py`):
- `compute_priority_score(subject: str, sender: str, category_label: str)` → `float`
  - Urgent keywords: +10 | deadline keywords: +5 | boss/manager domains: +5
  - Category boost: important +5, business +3, private +2
- `compute_confidence(spam_score: float, category_confidence: float)` → `float`
  - Formula: `(1 - spam_score) * category_confidence`

**ModelLoader** (`app/ai/model_loader.py`):
- `save_model(model, vectorizer, path)` / `load_model(path)` — pickle serialization

**6 Classification Categories**:
| Category | Keywords |
|----------|----------|
| `business` | invoice, meeting, proposal, client, contract, quote |
| `private` | family, personal, invitation, social, dinner |
| `important` | urgent, ASAP, deadline, critical, immediate |
| `other_work` | timesheet, sprint, JIRA, PR, pull request, standup |
| `others` | newsletter, notification, general, update, weekly |
| `spam` | buy now, click here, free, limited offer, act now |

---

### 6.3 Database (SQLAlchemy)

**Files**: `app/storage/db.py`, `app/storage/models.py`, `app/storage/repository.py`

**Engine & Session** (`app/storage/db.py`):
- `engine = create_engine(settings.effective_database_url)`
- `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
- `init_db()` — creates all tables
- `get_db()` — FastAPI dependency yielding `Session`

**ORM Models** (`app/storage/models.py`):

**`EmailRecord`** — `email_records` table
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto |
| `provider` | String(50) | — |
| `message_id` | String(255) | Unique, index |
| `sender` | String(255) | Index |
| `recipients` | Text | JSON array |
| `subject` | String(512) | — |
| `body_text` | Text | — |
| `body_html` | Text | Nullable |
| `received_at` | DateTime | — |
| `thread_id` | String(255) | Nullable |
| `attachments_count` | Integer | Default 0 |
| `language` | String(10) | Nullable |
| `ingested_at` | DateTime | Default utcnow |

Relationships: `predictions`, `feedback`, `audit_logs`

**`PredictionRecord`** — `prediction_records` table
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto |
| `email_id` | Integer | FK → email_records.id |
| `spam_score` | Float | — |
| `spam_label` | String(10) | — |
| `category_label` | String(50) | Index |
| `category_confidence` | Float | — |
| `priority_score` | Float | — |
| `routed_folder` | String(100) | — |
| `routed_action` | String(50) | — |
| `created_at` | DateTime | Default utcnow |

**`FeedbackRecord`** — `feedback_records` table
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto |
| `email_id` | Integer | FK → email_records.id |
| `old_label` | String(50) | — |
| `corrected_label` | String(50) | — |
| `corrected_by` | String(255) | — |
| `corrected_at` | DateTime | Default utcnow |
| `note` | Text | Nullable |

**`AuditLog`** — `audit_logs` table
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, auto |
| `email_id` | Integer | FK → email_records.id, nullable |
| `event_type` | String(50) | Index |
| `event_payload` | Text | JSON |
| `created_at` | DateTime | Default utcnow |

**Repositories** (`app/storage/repository.py`):
- `EmailRepository` — `add()`, `get()`, `get_by_message_id()`, `list_all()`, `count()`, `delete_old_spam()`
- `PredictionRepository` — `add()`, `list_by_email()`
- `FeedbackRepository` — `add()`, `list_all()`, `get_feedback_for_retrain()`
- `AuditLogRepository` — `add()`, `list_by_email()`

**Legacy models**: `data/models/models.py` has an alternate schema.

---

### 6.4 Authentication (OAuth2)

**Files**: `app/core/auth.py`, `app/api/auth_routes.py`

**OAuth2 Flows** (`app/core/auth.py`):
- `init_gmail_flow()` — creates `Flow` from `google_auth_oauthlib` with Gmail SCOPES
- `init_outlook_flow()` — builds Microsoft Graph OAuth2 URL manually
- `encrypt_token(token_data: dict)` → `str` — Fernet encryption with PBKDF2 key derivation
- `decrypt_token(encrypted_token: str)` → `dict` — reverse of encrypt

**SCOPES**: `["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"]`

**Routes** (`app/api/auth_routes.py`):
- `/auth/gmail/login` — generates OAuth URL, stores state
- `/auth/gmail/callback` — exchanges code, encrypts token, stores in DB
- `/auth/outlook/login` — generates Microsoft OAuth URL
- `/auth/outlook/callback` — exchanges code, encrypts token

---

### 6.5 Email Ingestion

**Files**: `app/ingestion/__init__.py`, `gmail_client.py`, `imap_client.py`, `outlook_client.py`

**NormalizedEmail** dataclass (`app/ingestion/__init__.py`):
```python
@dataclass
class NormalizedEmail:
    provider: str           # "gmail" | "outlook" | "imap"
    message_id: str
    sender: str
    recipients: List[str]
    subject: str
    body_text: str
    body_html: Optional[str]
    received_at: datetime
    thread_id: Optional[str]
    attachments_count: int
```

**GmailClient** (`app/ingestion/gmail_client.py`):
- `fetch_unseen()` → `List[NormalizedEmail]` — uses Gmail API v1 `users.messages.list` with `q=is:unseen`
- `parse_message(msg_id, msg_data)` → `NormalizedEmail` — extracts headers, payload parts, decodes base64
- `mark_as_read(msg_id)` / `move_to_folder(msg_id, folder)` — label modification

**IMAPClient** (`app/ingestion/imap_client.py`):
- `fetch_unseen()` → `List[NormalizedEmail]` — IMAP SSL, `SELECT INBOX`, `SEARCH UNSEEN`
- `parse_email(msg_data)` → `NormalizedEmail` — MIME parsing with `email` stdlib
- `mark_as_read(msg_id)` / `move_to_folder(msg_id, folder)` — IMAP STORE + COPY + STORE \Deleted

**OutlookClient** (`app/ingestion/outlook_client.py`):
- `fetch_unseen()` → `List[NormalizedEmail]` — Microsoft Graph API `GET /me/messages?filter=isRead eq false`
- `parse_email(msg_data)` → `NormalizedEmail` — JSON body, extracts `bodyPreview` as text
- `mark_as_read(msg_id)` / `move_to_folder(msg_id, folder)` / `trash(msg_id)` — PATCH + POST Graph API

---

### 6.6 Preprocessing

**Files**: `app/preprocessing/parser.py`, `cleaner.py`, `dedupe.py`

**Parser** (`app/preprocessing/parser.py`):
- `parse_email_address(raw: str)` → `(name: str, email: str)` — regex extraction
- `extract_domain(email: str)` → `str` — domain from email address

**Cleaner** (`app/preprocessing/cleaner.py`):
- `clean_body(text: str, html: Optional[str] = None)` → `str` — full pipeline
- `strip_html(html: str)` → `str` — BeautifulSoup `get_text(separator=' ')`
- `remove_signature(body: str)` → `str` — strips lines after `-- \n` or `--\n`
- `remove_quoted_replies(body: str)` → `str` — strips lines starting with `>` or `On ... wrote:`

**Dedupe** (`app/preprocessing/dedupe.py`):
- `content_hash(text: str)` → `str` — SHA-256 of cleaned body
- `is_duplicate(db: Session, text: str)` → `bool` — checks hash in session cache
- Session-level cache: `_session_hashes: Set[str]`

---

### 6.7 Routing Engine

**Files**: `app/routing/router.py`, `actions.py`, `rules.py`

**Router** (`app/routing/router.py`):
- `route_email(spam_score, spam_label, category_label, category_confidence)` → `(folder: str, action: str)`
  1. If spam → `("Spam", "delete_after_30_days")`
  2. If confidence < threshold → `("Review Queue", "send_to_review")`
  3. Lookup category in `FOLDER_MAP`

**Actions** (`app/routing/actions.py`):
- `EmailActions` — follows `FOLDER_MAP` actions

**Rules** (`app/routing/rules.py`):
- `RoutingRule` dataclass: `category: str, folder: str, action: str`
- `FOLDER_MAP`:
  | Category | Folder | Action |
  |----------|--------|--------|
  | spam | Spam | delete_after_30_days |
  | private | Private | move_to_folder |
  | business | Business | move_to_folder |
  | other_work | Other Work | archive |
  | others | Others | archive |
  | important | Important | move_to_folder |
- `DEFAULT_RULES` — list of `RoutingRule` from `FOLDER_MAP`

---

### 6.8 Scheduled Jobs (APScheduler)

**Files**: `app/jobs/sync_job.py`, `cleanup.py`, `retrain_job.py`

**Sync Job** (`app/jobs/sync_job.py`):
- `sync_imap()` — full pipeline:
  1. Create `IMAPClient`
  2. Fetch unseen emails → `List[NormalizedEmail]`
  3. For each: clean → classify → route → store (via APIs/direct DB)
  4. Uses `EmailClassifier`, `SpamDetector`, `Router`

**Cleanup** (`app/jobs/cleanup.py`):
- `cleanup_spam()` — deletes `EmailRecord`s where routed_folder="Spam" and age > `spam_retention_days`
- Uses `EmailRepository.delete_old_spam()`

**Retrain** (`app/jobs/retrain_job.py`):
- `scheduled_retrain()` — calls `retrain_classifier()` from `app/feedback/retrain.py`

**Scheduler registration**: In `app/main.py`, APScheduler starts with three jobs:
- `sync_imap` — interval `imap_poll_interval` (default 300s)
- `cleanup_spam` — interval daily
- `scheduled_retrain` — interval weekly

---

### 6.9 Frontend / Monitoring

**Files**: `app/templates/dashboard.html`, `app/monitoring/metrics.py`

**Dashboard** (`app/templates/dashboard.html`, 726 lines):
- Glassmorphism design (CSS `backdrop-filter: blur`, semi-transparent backgrounds)
- Metrics cards: total emails, spam rate, categories distribution, priority breakdown
- Email table: paginated list with spam badge, category, priority, routing folder
- Action buttons: retrain, cleanup
- Google Fonts (Inter) + CSS custom properties
- Auto-refresh via `dashboard_refresh_interval`

**Metrics** (`app/monitoring/metrics.py`):
- `get_metrics(db: Session)` → `MetricsResponse`
  - `total_emails`, `total_spam`, `spam_rate`
  - `category_distribution` → `Dict[str, int]`
  - `priority_distribution` → `Dict[str, int]`
  - `recent_activity` → recent predictions
  - `feedback_count`
  - `avg_confidence`

---

### 6.10 Deployment

**Files**: `deploy/Dockerfile`, `deploy/docker-compose.yml`, `deploy/nginx.conf`

**Dockerfile** (`deploy/Dockerfile`):
- Base: `python:3.11-slim`
- Installs: `pip install -r requirements.txt`
- Copies `app/`, `data/`, `scripts/`
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Docker Compose** (`deploy/docker-compose.yml`, version 3.9):
| Service | Image | Ports | Depends On |
|---------|-------|-------|------------|
| `app` | build: `.` | `8000:8000` | `db` |
| `db` | `postgres:15-alpine` | `5432:5432` | — |
| `spamassassin` | `instantlinux/spamassassin` | `783:783` | — |

- Environment: `USE_POSTGRES=true`, `DATABASE_URL` → PostgreSQL, `SPAMASSASSIN_ENABLED=true`
- Volumes: `pgdata` for PostgreSQL, `./data` for models

**Nginx** (`deploy/nginx.conf`):
- Listen on port 80
- Proxy pass to `http://app:8000`
- Standard reverse proxy headers

---

### 6.11 Testing

**Files**: `tests/` (8 files, ~45 tests)

| File | Tests | Scope |
|------|-------|-------|
| `test_classifier.py` | 10 | Categories, priority scoring, confidence |
| `test_cleanup.py` | 2 | Retention config, cleanup execution |
| `test_hf_classifier.py` | 3 | HF init, fallback, integration |
| `test_ingestion.py` | 8 | NormalizedEmail, sender/recipient parsing, HTML stripping, cleaning |
| `test_router.py` | 9 | Spam routing, low confidence, all categories |
| `test_spam_detector.py` | 6 | Spam detection, rules, sender impact |
| `test_spamassassin.py` | 5 | Client protocol, parsing, connection fallback |

**Framework**: pytest (configured in `pyproject.toml` under `[tool.pytest.ini_options]`)
**Conftest**: `tests/conftest.py` adds project root to `sys.path`

---

## 7. Keywords & Index

### Config Variable Names
```
app_name, debug, secret_key, encryption_key, database_url
use_postgres, postgres_user, postgres_password, postgres_host, postgres_port, postgres_db
gmail_client_id, gmail_client_secret, gmail_redirect_uri
outlook_client_id, outlook_client_secret, outlook_redirect_uri, outlook_tenant
imap_poll_interval
spam_model_path, classifier_model_path, vectorizer_path
spam_threshold, confidence_threshold, spam_retention_days, dashboard_refresh_interval
spamassassin_enabled, spamassassin_host, spamassassin_port
hf_enabled, hf_model_name
```

### Legacy Config Variables
```
APP_NAME, DATABASE_URL, IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD, IMAP_INBOX
SPAM_THRESHOLD, LOW_CONFIDENCE_THRESHOLD, AUTO_DELETE_DAYS
```

### API Route Paths
```
GET    /dashboard
GET    /docs
POST   /api/ingest/email
POST   /api/classify/email
POST   /api/route/email
GET    /api/emails
GET    /api/emails/{id}
POST   /api/feedback
GET    /api/metrics
POST   /api/retrain
POST   /api/cleanup/spam
GET    /auth/gmail/login
GET    /auth/gmail/callback
GET    /auth/outlook/login
GET    /auth/outlook/callback
```

### Class Names (with file locations)
```
Settings                    app/core/settings.py:5
EmailClassifier             app/ai/classifier.py:15
HFEmailClassifier           app/ai/hf_classifier.py:10
SpamDetector                app/ai/spam_detector.py:40
SpamAssassinSpamDetector    app/ai/spam_detector.py:10
RuleBasedSpamDetector       app/ai/spam_detector.py:25
SpamAssassinClient          app/ai/spamassassin_client.py:8
ModelLoader                 app/ai/model_loader.py:5
NormalizedEmail             app/ingestion/__init__.py:8
GmailClient                 app/ingestion/gmail_client.py:15
IMAPClient                  app/ingestion/imap_client.py:15
OutlookClient               app/ingestion/outlook_client.py:15
EmailActions                app/routing/actions.py:5
RoutingRule                 app/routing/rules.py:5
EmailRecord                 app/storage/models.py:10
PredictionRecord            app/storage/models.py:35
FeedbackRecord              app/storage/models.py:55
AuditLog                    app/storage/models.py:70
EmailRepository             app/storage/repository.py:10
PredictionRepository        app/storage/repository.py:45
FeedbackRepository          app/storage/repository.py:65
AuditLogRepository          app/storage/repository.py:85
```

### Key Function Signatures
```python
# app/ai/classifier.py
classify(text: str) -> tuple[str, float]  # (category_label, confidence)

# app/ai/spam_detector.py
detect(text: str, sender: str) -> tuple[bool, float]  # (is_spam, spam_score)

# app/ai/scorer.py
compute_priority_score(subject: str, sender: str, category_label: str) -> float
compute_confidence(spam_score: float, category_confidence: float) -> float

# app/ai/spamassassin_client.py
check_spam(text: str) -> tuple[bool, float]

# app/routing/router.py
route_email(spam_score, spam_label, category_label, category_confidence) -> tuple[str, str]

# app/preprocessing/cleaner.py
clean_body(text: str, html: Optional[str] = None) -> str
strip_html(html: str) -> str
remove_signature(body: str) -> str
remove_quoted_replies(body: str) -> str

# app/preprocessing/dedupe.py
content_hash(text: str) -> str
is_duplicate(db: Session, text: str) -> bool

# app/feedback/capture.py
capture_feedback(db: Session, email_id: int, old_label: str, corrected_label: str, corrected_by: str, note: Optional[str]) -> FeedbackRecord

# app/feedback/retrain.py
retrain_classifier(db: Session) -> dict

# app/monitoring/metrics.py
get_metrics(db: Session) -> MetricsResponse

# app/storage/db.py
init_db() -> None
get_db() -> Generator[Session]

# app/core/auth.py
init_gmail_flow() -> Flow
init_outlook_flow() -> dict
encrypt_token(token_data: dict) -> str
decrypt_token(encrypted_token: str) -> dict
```

### Database Column Names
```
EmailRecord:      id, provider, message_id, sender, recipients, subject, body_text, body_html, received_at, thread_id, attachments_count, language, ingested_at
PredictionRecord: id, email_id, spam_score, spam_label, category_label, category_confidence, priority_score, routed_folder, routed_action, created_at
FeedbackRecord:   id, email_id, old_label, corrected_label, corrected_by, corrected_at, note
AuditLog:         id, email_id, event_type, event_payload, created_at
```

### Pydantic Model Fields (API Schemas)
```
IngestEmailRequest:   sender, recipients, subject, body, provider, message_id, received_at, thread_id (opt)
ClassifyRequest:      text
ClassifyResponse:     spam_score, is_spam, category_label, category_confidence, priority_score, routed_folder, routed_action
RouteResponse:        spam_score, is_spam, category_label, category_confidence, priority_score, routed_folder, routed_action, ingested, email_id
FeedbackRequest:      email_id, corrected_label, note (opt)
EmailListResponse:    emails (list), total, page, page_size
EmailDetailResponse:  email + predictions (list)
MetricsResponse:      total_emails, total_spam, spam_rate, category_distribution, priority_distribution, recent_activity, feedback_count, avg_confidence
```

### Routing Rules / Folder Names
```
Category:     spam, private, business, other_work, others, important
Folders:      Spam, Private, Business, Other Work, Others, Important, Review Queue
Actions:      delete_after_30_days, move_to_folder, archive, send_to_review
```

### Script Commands
```
python run.py                              # Start dev server (uvicorn --reload :8000)
uvicorn app.main:app --reload --port 8000  # Alternative start
pip install -r requirements.txt            # Install dependencies
python scripts/train_model.py              # Train initial model
python scripts/evaluate_model.py           # Evaluate model on samples
python scripts/seed_labels.py             # Initialize DB + audit log
pytest tests/ -v                           # Run all tests
docker-compose -f deploy/docker-compose.yml up -d   # Start all services
docker-compose -f deploy/docker-compose.yml down    # Stop all services
```

---

## 8. Scripts & Commands Reference

| Command | File | Description |
|---------|------|-------------|
| `python run.py` | `run.py` | Start uvicorn dev server with `--reload` on port 8000 |
| `uvicorn app.main:app --reload --port 8000` | — | Alternative dev server |
| `pip install -r requirements.txt` | `requirements.txt` | Install all pinned dependencies |
| `python scripts/train_model.py` | `scripts/train_model.py` | Train LogisticRegression + TF-IDF on 6 categories (27 samples), outputs `.pkl` files |
| `python scripts/train_model.py --output data/models` | `scripts/train_model.py` | Custom output directory |
| `python scripts/evaluate_model.py` | `scripts/evaluate_model.py` | Evaluate on 10 test samples, prints classification report |
| `python scripts/seed_labels.py` | `scripts/seed_labels.py` | Initialize database tables + seed audit log |
| `pytest tests/ -v` | `tests/*` | Run all tests verbose |
| `pytest tests/test_classifier.py` | `tests/test_classifier.py` | Run specific test file |
| `docker-compose -f deploy/docker-compose.yml up -d` | `deploy/docker-compose.yml` | Deploy: app + postgres + spamassassin |
| `docker-compose -f deploy/docker-compose.yml logs -f` | — | Follow all container logs |
| `docker-compose -f deploy/docker-compose.yml down` | — | Stop all containers |

---

## 9. Dependencies Map

### From `requirements.txt` (pinned — installed in .venv)

| Package | Version | Category |
|---------|---------|----------|
| fastapi | 0.136.3 | Web Framework |
| uvicorn | 0.49.0 | ASGI Server |
| starlette | 1.3.1 | ASGI Toolkit |
| pydantic | 2.13.4 | Validation |
| pydantic-settings | 2.14.1 | Config |
| sqlalchemy | 2.0.50 | ORM |
| jinja2 | 3.1.6 | Templates |
| python-dotenv | 1.2.2 | Env Loading |
| apscheduler | 3.11.2 | Scheduling |
| scikit-learn | 1.9.0 | ML |
| numpy | 2.4.6 | Numerical |
| scipy | 1.17.1 | Scientific |
| joblib | 1.5.3 | Serialization |
| beautifulsoup4 | 4.15.0 | HTML Parsing |
| imapclient | 3.1.0 | IMAP |
| requests | 2.34.2 | HTTP |
| cryptography | 49.0.0 | Encryption |
| pytest | 9.0.3 | Testing |
| tzlocal | 5.3.1 | Timezone |
| tzdata | 2026.2 | Timezone Data |
| typing_extensions | 4.15.0 | Type Hints |

NOTES:
- `pyproject.toml` uses minimum versions with `>=`; `requirements.txt` pins exact versions.
- Gmail (`google-api-python-client`, `google-auth-oauthlib`) and HF (`transformers`, `torch`) packages are in `pyproject.toml` as >= requirements but are NOT installed in the current `.venv` (features gated behind config flags).

---

> *End of Project Analysis — All stacks, files, configurations, and keywords documented.*
