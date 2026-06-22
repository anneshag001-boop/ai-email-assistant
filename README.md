# AI Email Assistant

Open-source email classification and routing powered by **Groq AI**.  
Emails are automatically classified into **5 containers** — no manual review needed.

**Containers**: Private, Business, Other Work, Others, Spam

**Cost**: $0 — no cloud services, no credit card required.

---

## Quick Start (Local)

```bash
pip install -r requirements.txt
python run.py
```

Open **http://localhost:8000** → Register → Connect Gmail with App Password.

---

## Share Publicly (Zero Cost, No Credit Card)

Choose your deployment option:

### A) Quick Tunnel — No Account Needed

Random public URL, changes on restart. Takes 30 seconds.

| Platform | Command |
|----------|---------|
| **Windows** | Double-click `start_cloudflare.bat` |
| **Mac / Linux** | `bash deploy/start.sh` |
| **Docker** | `docker compose -f deploy/docker-compose.yml --profile tunnel up -d` |

**Result:** `https://random-words.trycloudflare.com`

### B) Named Tunnel — Permanent URL (Free Cloudflare Account)

Permanent public URL that survives restarts. Requires free Cloudflare account (no card).

```bash
cloudflared tunnel login          # browser → sign up (free)
cloudflared tunnel create ai-email
cloudflared tunnel route dns ai-email your-name.duckdns.org
cloudflared tunnel run ai-email
```

See `deploy/guide.md` for full instructions and config templates.

### C) Tailscale Funnel — One Command

```bash
tailscale up                      # sign in (free, no card)
tailscale funnel 8000             # one command
```

**Result:** `https://machine-name.tailabcdef.ts.net`

---

## Architecture

```
Browser ──HTTPS──► Cloudflare Tunnel ──► FastAPI ──► SQLite
```

- **Auth**: Email + password with JWT tokens, bcrypt hashing
- **AI**: Groq API (free tier, 30 req/min) or keyword fallback
- **Email**: IMAP (receive) + SMTP (send) via Gmail App Passwords
- **Sync**: APScheduler auto-polls every 5 minutes
- **Storage**: SQLite (one file, zero setup)

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

## Deploy Directory

| File | Purpose |
|------|---------|
| `deploy/guide.md` | Full zero-cost deployment guide (all options) |
| `deploy/start.sh` | Mac/Linux quick tunnel script |
| `deploy/Dockerfile` | Container image build |
| `deploy/docker-compose.yml` | Docker deployment with optional cloudflared sidecar |
| `deploy/cloudflared/config.yml` | Named tunnel configuration template |
| `deploy/nginx.conf` | Reverse proxy config (optional) |
| `render.yaml` | Render.com blueprint (optional, requires account) |
