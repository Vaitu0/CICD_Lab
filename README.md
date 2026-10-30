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
    ├── nginx        :80  (public)  static frontend + reverse proxy
    │                    /          → apps/frontend
    │                    /app/      → hello-app:5000   (internal only)
    │                    /grafana/  → grafana:3000     (internal only)
    ├── hello-app    FastAPI — no host port (expose 5000 on Compose network)
    ├── grafana      dashboards — no host port (expose 3000 on Compose network)
    └── zabbix-*     server, web, db, agent (still published on host ports)
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

### Useful URLs (when nginx listens on the host)

| Service | URL |
|---------|-----|
| Frontend (nginx) | http://127.0.0.1/ |
| API (via nginx only) | http://127.0.0.1/app/ and `/app/health` |
| Grafana (via nginx only) | http://127.0.0.1/grafana/ |
| Zabbix UI | http://127.0.0.1:8080/ |

**Port lock:** `hello-app` and `grafana` use `expose` only — they are reachable on the Compose network (and from nginx), **not** as `localhost:5000` / `localhost:3000` on the host. CI health checks still use `http://hello-app:5000` and `http://grafana:3000` inside that network.

Grafana is configured with `GF_SERVER_SERVE_FROM_SUB_PATH=true` and `GF_SERVER_ROOT_URL` for the `/grafana/` path.

Default Zabbix UI login is often `Admin` / `zabbix` — change it after first login.

### Environment variables / secrets

1. Copy the template on the server:  
   `cp infrastructure/.env.example infrastructure/.env`
2. Fill in real values in `.env` only (gitignored).
3. Never commit `.env`. The example file has **names and safe placeholders only**.

| Variable | Role |
|----------|------|
| `VPN_IP` | Host bind for published ports (`127.0.0.1`, `0.0.0.0`, or LAN/VPN IP) |
| `ZABBIX_PORT` | Zabbix web host port (still published) |
| `APP_PORT` / `GRAFANA_PORT` | Optional leftovers in `.env`; **not** used for host publish after the port lock |
| `POSTGRES_*` | Zabbix database credentials |
| `IMAGE_TAG` | Local/manual image tag (`dev`). **CI sets this to the git SHA** |

CI uses `docker compose --env-file $HOME/.../infrastructure/.env` so secrets stay in one place on the server and are **not** copied into the Actions work directory.

## CI/CD

### Build & deploy (`.github/workflows/build.yml`)

- **Trigger:** push to `main` when paths under `infrastructure/`, `apps/`, or the workflow file change
- **Runner:** `self-hosted`
- **Steps:**
  1. Checkout
  2. `docker compose --env-file` pointing at the server’s persistent `.env` (SHA tag from the job)
  3. Build + `up -d` for nginx, grafana, hello-app
  4. Health checks on the Compose network (`curlimages/curl` → `nginx`, `grafana`, `hello-app`)

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
- Port lock: public entry via nginx only for app and Grafana
- Separating app code (`apps/`) from infra (`infrastructure/`)
- Frontend calling the API through the proxy (`script.js`)
- Basic observability with Zabbix + Grafana
- Secrets via server-side `.env` + Compose `--env-file` in CI

## Roadmap / ideas

- Proxy Zabbix under `/zabbix/` (and stop publishing `:8080` if desired)
- Optional later: GitHub Actions secrets for non-homelab runners
- Move the stack to a VPS; optional Terraform later
- Container registry (e.g. GHCR)

## License

Personal learning project. Use and adapt freely for your own labs.
