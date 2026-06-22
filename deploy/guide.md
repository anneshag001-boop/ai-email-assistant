# Zero-Cost Deployment Guide

This project costs **$0 to deploy and run**. No cloud accounts, no credit cards, no monthly fees.

---

## Option A: Quick Tunnel (30 seconds, no account)

Your machine + one command = public HTTPS URL. URL changes on restart.

### Windows
```batch
start_cloudflare.bat
```
Or manually:
```batch
pip install -r requirements.txt
python run.py
cloudflared tunnel --url http://localhost:8000
```

### Mac / Linux
```bash
bash deploy/start.sh
```
Or manually:
```bash
pip install -r requirements.txt
python run.py &
cloudflared tunnel --url http://localhost:8000
```

**Result:** `https://random-words.trycloudflare.com`

**Pros:** Zero setup, no account needed.
**Cons:** Random URL each restart, tunnel stops when machine sleeps.

---

## Option B: Named Tunnel — Permanent URL (Free Cloudflare Account)

Get a permanent public URL that survives restarts.

### Step 1: Get a free domain
Use any of these (all free, no card):
- **DuckDNS** (https://duckdns.org) — `your-name.duckdns.org`
- **nip.io** — `your-ip.nip.io` (no registration)
- **Cloudflare** (free plan, no card) — use your own domain

### Step 2: Install cloudflared
```bash
# Mac/Linux
brew install cloudflare/cloudflare/cloudflared

# Windows
winget install Cloudflare.cloudflared
```

### Step 3: Authenticate (free Cloudflare account, no card)
```bash
cloudflared tunnel login
```
Opens a browser — sign up or log in with your free Cloudflare account.

### Step 4: Create a named tunnel
```bash
cloudflared tunnel create ai-email
```
This creates a credentials file at `~/.cloudflared/`.

### Step 5: Create config
Save as `~/.cloudflared/config.yml` (or use `deploy/cloudflared/config.yml` as template):
```yaml
tunnel: ai-email
credentials-file: /home/user/.cloudflared/ai-email.json
ingress:
  - hostname: your-name.duckdns.org
    service: http://localhost:8000
  - service: http_status:404
```

### Step 6: Point DNS
```bash
# Add a CNAME or A record in your DNS panel pointing to: ai-email.cfargotunnel.com
cloudflared tunnel route dns ai-email your-name.duckdns.org
```

### Step 7: Run it
```bash
cloudflared tunnel run ai-email
```

**Result:** `https://your-name.duckdns.org` — permanent, HTTPS, survives restarts.

**Pros:** Permanent URL, set-it-and-forget-it.
**Cons:** Requires free Cloudflare account + free DuckDNS registration.

### Docker version
```bash
docker compose -f deploy/docker-compose.yml up -d
```
The included `cloudflared` sidecar creates a quick tunnel automatically. For named tunnel, mount your credentials:
```yaml
volumes:
  - ~/.cloudflared:/etc/cloudflared
command: tunnel run ai-email
```

---

## Option C: Tailscale Funnel (One Command, No Card)

[Tailscale](https://tailscale.com) is free for personal use. Funnel exposes a local port publicly with HTTPS.

### Step 1: Install Tailscale
```bash
# Mac/Linux
curl -fsSL https://tailscale.com/install.sh | sh

# Windows
winget install Tailscale.Tailscale
```

### Step 2: Sign in (free account, no card needed)
```bash
tailscale up
```

### Step 3: Enable Funnel
```bash
tailscale funnel 8000
```

**Result:** `https://machine-name.tailabcdef.ts.net` — permanent, HTTPS.

**Pros:** One command, permanent URL, no DNS setup.
**Cons:** Requires Tailscale account (free, no card). Subdomain is random.

### To stop:
```bash
tailscale funnel 8000 off
```

---

## Option D: Docker on Any Free Host

Use the updated `docker-compose.yml` on any machine with Docker:
```bash
docker compose -f deploy/docker-compose.yml up -d
```

This starts the app + optional `cloudflared` sidecar for tunneling. Works on:
- Your own machine
- A Raspberry Pi at home
- Any free Docker host (Oracle Cloud free tier, etc.)

---

## Comparison

| Option | URL | Needs Account? | Needs Card? | Survives Reboot? |
|--------|-----|----------------|-------------|------------------|
| Quick Tunnel | Random | No | No | No |
| Named Tunnel | Permanent | Cloudflare (free) | No | Yes |
| Tailscale Funnel | Random subdomain | Tailscale (free) | No | Yes |
| Docker | Any of above | Varies | No | Yes |

---

## Production Checklist (Still $0)

1. **Set a strong SECRET_KEY** in `.env`
2. **Set a strong ENCRYPTION_KEY** in `.env` (32+ random bytes)
3. **Add GROQ_API_KEY** for AI classification (free tier: 30 req/min)
4. **Set OLLAMA_ENABLED=false** when using Groq
5. **Use Option B (named tunnel)** for a permanent URL
6. **Run as a system service** so it auto-starts on boot
