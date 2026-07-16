# init-db — Initialize or reset the database

Rebuild the database schema and load example data from scratch.

## Prerequisites
- Virtual environment activated
- `backend/.env` configured with `DATABASE_URL` and `SQLITE_FALLBACK_URL`

## Steps

```bash
cd backend
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py

1. `init_db.py --rebuild`: Drops all tables and recreates from SQLAlchemy models
2. `generate_example_data.py`: Generates 18 JSON seed files in `backend/example/`
3. `load_example_data.py`: Loads those JSON files into the database via service layer
```

## Important

- `--rebuild` is destructive. It drops all existing tables
- If OceanBase is unreachable, system auto-falls-back to SQLite
- Run `pytest` afterward to verify the setup works
