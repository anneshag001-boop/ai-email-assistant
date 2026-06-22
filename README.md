# AI Email Assistant

Open-source email classification and routing powered by **Groq AI**.  
Emails are automatically classified into **5 containers** — no manual review needed.

**Containers**: Private, Business, Other Work, Others, Spam

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Run
```bash
python run.py
```
Or double-click `run.bat`.

Open **http://localhost:8000** → Register → Connect Gmail with App Password.

## Share Publicly (Zero Cost, No Credit Card)

Double-click **`start_cloudflare.bat`** — it installs `cloudflared` automatically and creates a public URL like `https://something.trycloudflare.com`. Share that URL with anyone.

Works on any machine (Windows/Mac/Linux). No server, no cloud account, no credit card.

## Architecture

```
Browser ──HTTPS──► Cloudflare Tunnel ──► FastAPI ──► SQLite
                          │
                    No account needed
                    (trycloudflare.com)
```

- **Auth**: Email + password with JWT tokens, bcrypt hashing
- **AI**: Groq API (free tier, 30 req/min) or keyword fallback
- **Email**: IMAP (receive) + SMTP (send) via Gmail App Passwords
- **Sync**: APScheduler auto-polls every 5 minutes
- **Storage**: SQLite (one file, zero setup)
- **Cost**: $0 — no cloud services, no credit card required

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register with optional Gmail App Password |
| POST | `/auth/login` | Login |
| GET | `/dashboard` | Main dashboard |
| POST | `/api/accounts` | Add email account |
| POST | `/api/accounts/{id}/sync` | Sync IMAP |
| POST | `/api/feedback` | Correct AI classification |
| POST | `/api/compose` | Send email |
| POST | `/api/reply/{id}` | Reply to email |

## Deploy to Cloud (Optional)

If you want 24/7 uptime without running your own machine:

- **Render.com** (no credit card): Connect your GitHub repo, use `render.yaml`
- **Fly.io** (credit card required): Use `fly.toml`
