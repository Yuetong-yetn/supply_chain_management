---
name: run-dev
description: Use when starting the FastAPI backend development server and checking /api/health or /api/health/db.
---

# run-dev — Start the backend development server

Start the FastAPI development server for this project.

## Prerequisites
- Python virtual environment exists at `backend/.venv`
- Dependencies installed via `backend/requirements.txt`
- `.env` file configured at `backend/.env`

## Steps
1. Activate the virtual environment
2. cd into `backend/`
3. Run `uvicorn app.main:app --reload --port 8000`

## Post-start
The server runs at http://127.0.0.1:8000 with:
- Demo UI: http://127.0.0.1:8000/demo
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health
- DB health: http://127.0.0.1:8000/api/health/db

## For shared access
Run with `--host 0.0.0.0`:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes
- The server mounts `frontend/` as static files at `/ui`
- API routes are registered in `backend/app/main.py`
- Hot reload watches `backend/app/` directory
