# CICD Lab

Homelab project for learning **DevOps / CI/CD**: Docker Compose stack, GitHub Actions on a **self-hosted runner**, reverse proxy, monitoring (Zabbix + Grafana), and a small FastAPI app with a static frontend.

Built and iterated on a Linux ARM server (Debian) as a personal learning lab — not a production system.

## Architecture

```text
GitHub (push to main)
    │
    ▼
Self-hosted runner (SerwerPD)
    │  build → tag images with git SHA → deploy → health checks
    ▼
Docker Compose
    ├── nginx        :80   static frontend + reverse proxy
    │                    /app/      → hello-app:5000
    │                    /grafana/  → grafana:3000
    ├── hello-app    FastAPI (Uvicorn)
    ├── grafana      dashboards (Zabbix datasource)
    └── zabbix-*     server, web, db, agent (monitoring)
```

Images built by CI are tagged with `${{ github.sha }}` (e.g. `hello-app-image:<commit>`), not only `latest`.

## Repository layout

```text
CICD_Lab/
├── apps/
│   ├── backend/test/     # FastAPI app (Dockerfile, requirements)
│   └── frontend/         # Static HTML/CSS (mounted into nginx)
├── infrastructure/
│   ├── docker-compose.yml
│   ├── nginx/            # reverse proxy config + optional image build
│   ├── grafana/          # Grafana image
│   ├── .env.example      # env var names (no secrets)
│   └── .env              # local secrets (gitignored)
└── .github/workflows/
    ├── build.yml         # build + deploy + health checks
    └── cleaner.yml       # prune unused Docker data (schedule / manual)
```

## Stack

| Layer | Tech |
|--------|------|
| App | FastAPI + Uvicorn |
| Frontend | Static HTML/CSS |
| Proxy | nginx |
| Orchestration | Docker Compose |
| CI/CD | GitHub Actions (self-hosted runner) |
| Monitoring | Zabbix 7 + Grafana |
| Observability in Grafana | Web scenarios (e.g. response time for nginx / hello-app) |

## Prerequisites

- Docker Engine + Compose plugin
- Git
- (For CI) A registered [self-hosted runner](https://docs.github.com/en/actions/hosting-your-own-runners) on the same host, with permission to use Docker
- Outbound DNS/network for image pulls and `pip install` during builds

## Quick start (local)

```bash
cd infrastructure
cp .env.example .env
# edit .env — set VPN_IP, ports, Postgres credentials, IMAGE_TAG

docker compose up -d --build
```

### Useful URLs (defaults when `VPN_IP=0.0.0.0`)

| Service | URL |
|---------|-----|
| Frontend (nginx) | http://127.0.0.1/ |
| API via proxy | http://127.0.0.1/app/ and `/app/health` |
| API direct | http://127.0.0.1:5000/health |
| Grafana via proxy | http://127.0.0.1/grafana/ |
| Grafana direct | http://127.0.0.1:3000/ |
| Zabbix UI | http://127.0.0.1:8080/ |

Grafana is configured with `GF_SERVER_SERVE_FROM_SUB_PATH=true` and `GF_SERVER_ROOT_URL` for the `/grafana/` path.

Default Zabbix UI login is often `Admin` / `zabbix` — change it after first login.

### Environment variables

See `infrastructure/.env.example`. Never commit `.env`.

Typical keys: `VPN_IP`, `APP_PORT`, `GRAFANA_PORT`, `ZABBIX_PORT`, `POSTGRES_*`, `IMAGE_TAG`.

`VPN_IP` controls which host address ports bind to (`0.0.0.0`, `127.0.0.1`, or a LAN/VPN IP).

## CI/CD

### Build & deploy (`.github/workflows/build.yml`)

- **Trigger:** push to `main` when paths under `infrastructure/`, `apps/`, or the workflow file change
- **Runner:** `self-hosted`
- **Steps:**
  1. Checkout
  2. Copy host `.env` into the Compose project (secrets stay on the server)
  3. `docker compose build` nginx, grafana, hello-app
  4. `docker compose up -d` those services
  5. Health checks on the Compose network (`curlimages/curl` → `nginx`, `grafana`, `hello-app`)

### Cleaner (`.github/workflows/cleaner.yml`)

Manual and/or scheduled prune of unused Docker images/cache on the runner host (keeps disk under control).

## Monitoring notes

- Zabbix agent talks to `zabbix-server` on the Compose network; host interface should use **DNS** (`zabbix-agent`), not `127.0.0.1` inside the server container.
- HTTP checks / web scenarios target services by Compose DNS names where appropriate (e.g. `http://nginx/`, `http://hello-app:5000/`).
- Prefer **numeric** metrics (status code, response time) for Grafana graphs; HTML body items do not graph well.

## Development tips

- Frontend is bind-mounted into nginx (`../apps/frontend` → `/usr/share/nginx/html`). Edit HTML/CSS and refresh — no image rebuild required for static files.
- Backend changes need an image rebuild:  
  `docker compose up -d --build hello-app`
- After nginx config edits:  
  `docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload`

## What this lab demonstrates

- Self-hosted CI/CD end-to-end (not only cloud-hosted runners)
- Image tagging with git SHA
- Path-filtered workflows and post-deploy health checks
- Reverse proxy (path-based routing, Grafana subpath)
- Separating app code (`apps/`) from infra (`infrastructure/`)
- Basic observability with Zabbix + Grafana

## Roadmap / ideas

- Wire frontend JS to call `/app/` and `/app/health`
- Tighten secrets handling (less reliance on copying `.env` from `$HOME`)
- Stop publishing backend/Grafana ports; expose only via nginx
- Move the stack to a VPS; optional Terraform later
- Container registry (e.g. GHCR)

## License

Personal learning project. Use and adapt freely for your own labs.
