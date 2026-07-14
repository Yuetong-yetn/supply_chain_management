# Supply Chain Management — Agent Guide

## Project

Supply chain inventory collaboration & smart replenishment system for multi-warehouse/multi-store retail.  
Backend: **FastAPI + SQLAlchemy** (Python). Frontend: **vanilla HTML/CSS/JS** (served by FastAPI as static files).  
<<<<<<< Updated upstream
Primary docs and comments are in **Chinese**.
=======
All primary docs and comments are in **Chinese**.
>>>>>>> Stashed changes

## Commands (run from `backend/`)

```bash
# First time setup
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
<<<<<<< Updated upstream
Copy-Item .env.example .env

# Init DB & seed data (required before first start)
=======
Copy-Item .env.example .env     # then edit .env if needed

# Init DB & seed data
>>>>>>> Stashed changes
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py

# Start dev server
uvicorn app.main:app --reload --port 8000

# Run all tests (auto-creates test_suite.db, no external DB needed)
pytest -q
<<<<<<< Updated upstream

# Run a single test file
pytest tests/test_health.py -v
=======
>>>>>>> Stashed changes
```

## Database

<<<<<<< Updated upstream
- **Primary**: OceanBase (MySQL protocol). **Fallback**: SQLite (automatic).
- Engine selection at import time in `app/core/database.py:53` — probes OceanBase, falls back to SQLite on failure.
- Check runtime mode: `GET /api/health/db` (returns `oceanbase-primary` or `sqlite-fallback`).
- Tests always use `test_suite.db` — `conftest.py:12` sets `DATABASE_URL` env var **before** app imports.
- Test session (`pytest_sessionstart`) automatically rebuilds + reseeds the test DB.
=======
- **OceanBase** (MySQL protocol) is the primary DB; **SQLite** is the automatic fallback.
- Engine selection happens at import time in `app/core/database.py:53` — tries OceanBase, falls back to SQLite on failure.
- Check runtime DB mode via `GET /api/health/db` (returns `oceanbase-primary` or `sqlite-fallback`).
- Tests always use `test_suite.db` (set via `DATABASE_URL` env var in `conftest.py:12`), rebuilt + seeded fresh per session.
>>>>>>> Stashed changes

## Architecture

```
backend/
  app/
<<<<<<< Updated upstream
    main.py       — FastAPI entrypoint, registers 20 routers + exception handlers
    api/routers/  — One file per domain (products, inventory, recommendations, ...)
    core/         — config.py (.env), database.py (engine + auto-fallback), cache, response, exceptions
    models/       — 16+ SQLAlchemy ORM models
    schemas/      — Pydantic request/response models
    services/     — Business logic (one per domain); llm/ subpackage for AI routing
    utils/        — datetime, hash, number, pagination helpers
  scripts/        — init_db (--rebuild), generate/load/reset example data
  tests/          — conftest auto-bootstraps DB; 10 test files
  example/        — JSON seed data (one file per entity)
  schema/         — .db files + exported schema.sql / seed.sql
frontend/         — index.html, api.js, app.js, style.css (served at /ui/)
```

Entrypoint: `app/main.py:35-79` — creates FastAPI app, registers all routers explicitly.

## Key URLs
=======
    main.py          — FastAPI app entrypoint, exception handlers, mounts /ui/ static files
    api/routers/     — 20 routers, one per domain (products, inventory, recommendations, ...)
    core/            — config.py (.env settings), database.py (engine + fallback), cache, response, exceptions
    models/          — 16+ SQLAlchemy ORM models
    schemas/         — Pydantic request/response schemas
    services/        — Business logic (one per domain + llm/ sub-package for AI routing)
    utils/           — datetime, hash, number, pagination helpers
  scripts/           — init_db (rebuild flag), generate/load example data, reset demo
  tests/             — 10 test files; conftest.py auto-sets DATABASE_URL to test_suite.db
  schema/            — SQLite .db files, exported schema.sql and seed.sql
  example/           — JSON seed data files (one per entity)
frontend/
  index.html         — Skeleton for demo UI
  api.js             — Unified API request wrapper
  app.js             — Login, role views, dashboard, business interaction
```

Entrypoint: `app/main.py:35` creates the FastAPI app. All routers are registered explicitly at line 59-78.

## Key URLs (when server is running)
>>>>>>> Stashed changes

| URL | Purpose |
|---|---|
| `/demo` | Recommended demo entry (redirects to `/ui/`) |
| `/docs` | Swagger UI |
| `/api/health` | Basic health check |
| `/api/health/db` | Database runtime profile & mode |
| `/api/llm/status` | LLM provider/availability check |

## Login

<<<<<<< Updated upstream
Username = any name, password = `demo123`, pick role from dropdown.  
Pre-seeded accounts: `admin`/`buyer`/`warehouse`/`store`/`manager` with password `<username>123`.

## LLM Integration

Optional — core business works without it. Three providers in `backend/.env`:
- `LLM_PROVIDER=deepseek` (needs `DEEPSEEK_API_KEY`)
- `LLM_PROVIDER=ollama` (local, no key needed)
- `LLM_PROVIDER=rule` (default, no external calls)

Restart server after changing `.env`.

## Testing

- Uses `fastapi.testclient.TestClient`.
- `conftest.py` sets `DATABASE_URL=sqlite:///.../test_suite.db` **before** any `from app import ...` — this ordering is essential.
- `pytest_sessionstart` runs `init_db(rebuild=True)` + seed data generation + load.
- No external services required (LLM tests mock or use rule provider).
- Run from `backend/`: `pytest -q` or `pytest test_health.py -v`.
=======
Default credentials: username = any name, password = `demo123`, pick role from dropdown.  
Seeded user accounts: `admin`/`buyer`/`warehouse`/`store`/`manager`, all with password pattern `username`+`123`.

## LLM Integration

Optional — core business works without it. Three providers: `deepseek`, `ollama`, `rule`.  
Configure in `backend/.env` (`LLM_PROVIDER`, API keys, etc.). Restart server after changes.  
Rule provider (default if no API key configured) generates replenishment reasons locally.

## Testing Notes

- Tests use `fastapi.testclient.TestClient`.
- `conftest.py` sets `DATABASE_URL` to `test_suite.db` **before** any app imports — this is critical.
- `pytest_sessionstart` calls `init_db(rebuild=True)` + `generate_example_data()` + `load_example_data()`.
- No external services needed; LLM tests mock or use rule provider.
- Run from `backend/` directory: `pytest -q` or `pytest test_health.py -v`.
>>>>>>> Stashed changes
