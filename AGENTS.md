# AGENTS.md — Supply Chain Management

## Project structure

```
backend/       FastAPI app (Python 3.11+)
frontend/      Static HTML/CSS/JS (served by backend)
docs/          Project-level docs
```

## Quick start (backend)

```powershell
cd backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py
uvicorn app.main:app --reload --port 8000
```

## Dev commands

All commands run from `backend/` with `.venv` activated.

| Action | Command |
|---|---|
| Start dev server | `uvicorn app.main:app --reload --port 8000` |
| Init/reset DB | `python scripts/init_db.py --rebuild` |
| Load example data | `python scripts/generate_example_data.py` then `python scripts/load_example_data.py` |
| Run all tests | `pytest` |
| Run single test | `pytest tests/test_login.py -v` |
| Access URLs | Demo: `/demo`, API docs: `/docs`, Health: `/api/health` |

## Testing quirks

- `conftest.py` overrides `DATABASE_URL` env var to SQLite before any import — tests always use SQLite `backend/schema/test_suite.db`.
- Test session auto-rebuilds DB and loads seed + example data (`pytest_sessionstart`).
- The `api_client` fixture returns `fastapi.testclient.TestClient(app)`.
- No pytest config files exist; tests run via convention (`pytest` from `backend/`).

## Database

- Primary: OceanBase (MySQL-compatible via PyMySQL). SQLite as automatic fallback.
- Runtime fallback detection is **module-level** in `app/core/database.py` — happens once at import time.
- `backend/app/core/config.py` uses `pydantic-settings` with `lru_cache`; tests clear the cache via `get_settings.cache_clear()`.
- `.env` lives in `backend/` (not root). Root `.env` is ignored.

## API conventions

- All responses wrapped in `{"success": bool, "message": str, "data": any}`.
- Errors use `BusinessException` (custom), `RequestValidationError` (422), or `IntegrityError` (400).
- Login accepts `employee_no` as `username` field. Demo users: `admin`/`admin123`, `buyer`/`buyer123`, etc.

## LLM / AI

- Provider routing in `backend/app/services/llm/` — supports DeepSeek, Ollama, or `rule` (no external API).
- AI enhances replenishment reasons only; core logic still works without it.
- Check status: `GET /api/llm/status`.

## Notable

- No CI config, no pre-commit, no formatter/linter config in repo.
- `frontend/` is static — no build step.
- `backend/schema/` contains auto-generated `schema.sql` and `seed.sql` (SQLite only).
- `backend/.env` currently has a real DeepSeek API key — **do not commit**.
