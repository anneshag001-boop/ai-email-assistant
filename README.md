# AI Email Assistant

Autonomous email classification and routing powered by **Ollama SLM** (Small Language Model).  
Emails are automatically classified into **5 containers** — no manual review needed.

**Containers**: Private, Business, Other Work, Others, Spam

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Ensure Ollama is running
```bash
ollama serve                    # Start Ollama (if not running)
ollama pull llama3.2:3b         # Pull a small model (~1.9GB)
```
Other recommended models: `phi3:mini`, `mistral:7b`, `qwen2.5:7b`

### 3. Start the app
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Open the dashboard
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

## Architecture

```
Email Sources → Ingestion → Cleaner → Ollama SLM (classify) → Router → 5 Containers
```

1. **Ingestion**: Gmail API / Outlook Graph / IMAP
2. **Preprocessing**: HTML stripping, signature removal, deduplication
3. **SLM Classification**: Ollama model classifies into 1 of 5 categories
4. **Autonomous Routing**: Emails are moved/archived/trashed automatically
5. **Spam Cleanup**: Spam emails auto-deleted after 30 days

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ingest/email` | Ingest an email |
| POST | `/api/classify/email` | Classify + route |
| GET | `/api/emails` | List emails |
| POST | `/api/feedback` | Submit correction |
| GET | `/api/metrics` | System metrics |
| POST | `/api/retrain` | (No-op with SLM) |
| POST | `/api/cleanup/spam` | Delete old spam |

## Configuration

Edit `.env` or `app/core/settings.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_ENABLED` | `true` | Enable SLM classifier |
| `OLLAMA_HOST` | `localhost` | Ollama server host |
| `OLLAMA_PORT` | `11434` | Ollama server port |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model name for classification |
| `OLLAMA_TIMEOUT` | `30` | Request timeout in seconds |

## Classification Prompt

The SLM classifies emails using this category definition:

- **private** — Personal emails from friends/family, social invitations
- **business** — Trading websites, brand promotions, invoices, orders, business correspondence
- **other_work** — Bank alerts, OTP/passwords, login verification, Google Alerts, important app notifications
- **others** — Facebook, Instagram, social media, newsletters
- **spam** — Unsolicited bulk, scams, phishing, fake prizes

## Docker

```bash
docker-compose -f deploy/docker-compose.yml up -d
```

## Tests

```bash
pytest tests/ -v
```
