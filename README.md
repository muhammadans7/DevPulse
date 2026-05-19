# DevPulse

A multi-tenant SaaS API that aggregates GitHub activity for developer teams, scores velocity, and exposes org-level analytics. Built with FastAPI, PostgreSQL, and Redis.

---

## What it does

- Teams sign up and create an organization
- Connect GitHub via OAuth to pull commit and PR activity
- Background jobs sync activity from the GitHub API on a schedule
- REST endpoints expose velocity scores, contributor breakdowns, and org-level analytics
- Programmatic access via API keys (per org, multiple keys supported)
- Rate limiting per organization tier

---

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| ORM | SQLModel + Alembic |
| Database | PostgreSQL |
| Async HTTP | httpx |
| Task queue | ARQ (async Redis queue) |
| Cache / broker | Redis |
| Auth | JWT + GitHub OAuth2 |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |

---

## Project structure

```
devpulse/
├── app/
│   ├── main.py                  # FastAPI app factory + lifespan
│   ├── config.py                # Settings via pydantic-settings
│   ├── dependencies.py          # Shared DI — get_db, get_current_user
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Aggregates all v1 routers
│   │       ├── auth.py          # /auth — register, login, GitHub OAuth
│   │       ├── users.py         # /users
│   │       ├── orgs.py          # /orgs — create, invite, manage members
│   │       ├── repos.py         # /repos — connect and sync repos
│   │       └── analytics.py     # /analytics — velocity, contributors
│   ├── models/
│   │   ├── user.py
│   │   ├── org.py               # Organization + OrgMembership
│   │   ├── repo.py              # Repo + CommitSnapshot
│   │   └── api_key.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── org.py
│   │   ├── repo.py
│   │   └── analytics.py
│   ├── services/
│   │   ├── auth_service.py      # JWT, password hashing, OAuth flow
│   │   ├── github_service.py    # httpx calls to GitHub API
│   │   ├── analytics_service.py # Velocity scoring logic
│   │   └── api_key_service.py   # Key generation and validation
│   ├── workers/
│   │   ├── arq_worker.py        # ARQ worker entry point
│   │   └── tasks/
│   │       ├── sync_repos.py
│   │       └── sync_commits.py
│   ├── middleware/
│   │   ├── rate_limit.py
│   │   └── logging.py
│   └── db/
│       ├── session.py           # Async engine + session factory
│       └── init_db.py
├── alembic/
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_orgs.py
│   └── test_analytics.py
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## Getting started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/devpulse.git
cd devpulse
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

- `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` — create an OAuth app at [github.com/settings/developers](https://github.com/settings/developers)

### 5. Set up the database

```bash
# Create the database (if not already created)
sudo -u postgres psql -c "CREATE USER devpulse WITH PASSWORD 'devpulse';"
sudo -u postgres psql -c "CREATE DATABASE devpulse OWNER devpulse;"

# Run migrations
alembic upgrade head
```

### 6. Run the development server

```bash
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### 7. Run the background worker (separate terminal)

```bash
python -m app.workers.arq_worker
```

---

## Docker setup

```bash
docker-compose up --build
```

This starts the FastAPI app, PostgreSQL, and Redis together. Migrations run automatically on startup.

---

## Environment variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | JWT signing secret — keep this private |
| `GITHUB_CLIENT_ID` | GitHub OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth app client secret |
| `REDIS_URL` | Redis connection string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry (default: 30) |

---

## API overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET | `/api/v1/auth/github` | Start GitHub OAuth flow |
| GET | `/api/v1/auth/github/callback` | GitHub OAuth callback |
| POST | `/api/v1/orgs` | Create an organization |
| POST | `/api/v1/orgs/{id}/invite` | Invite a member |
| GET | `/api/v1/repos` | List connected repos |
| POST | `/api/v1/repos/sync` | Trigger a manual sync |
| GET | `/api/v1/analytics/velocity` | Org velocity score |
| GET | `/api/v1/analytics/contributors` | Contributor breakdown |

Full interactive docs available at `/docs` when the server is running.

---

## Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Database schema

| Table | Description |
|---|---|
| `users` | Registered DevPulse users |
| `organizations` | Tenant orgs |
| `org_memberships` | User ↔ org join table with roles |
| `repos` | GitHub repos connected to an org |
| `commit_snapshots` | Synced commit activity per repo |
| `api_keys` | Hashed API keys issued per org |

---

## Deployment

The app is designed to deploy on [Railway](https://railway.app) or [Render](https://render.com).

Set all environment variables from `.env.example` in your platform's dashboard. Point `DATABASE_URL` and `REDIS_URL` to your managed instances. Run `alembic upgrade head` as a pre-deploy command.

---

## License

MIT
