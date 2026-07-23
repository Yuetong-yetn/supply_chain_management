---
name: run-tests
description: Use when running pytest, a single backend test file, or checking the automated test suite status.
---

# run-tests — Run automated tests

Execute the pytest test suite for this project.

## Prerequisites
- Virtual environment activated
- `backend/tests/conftest.py` sets up test database automatically

## Commands

```bash
cd backend

# Run all tests
pytest

# Run a single test file
pytest tests/test_login.py -v

# Run a specific test function
pytest tests/test_health.py::test_health_check -v

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Test architecture
- Tests always use SQLite (`backend/schema/test_suite.db`). `conftest.py` overrides `DATABASE_URL` before any import
- `pytest_sessionstart` hook rebuilds DB and loads seed + example data automatically
- The `api_client` fixture provides `fastapi.testclient.TestClient(app)`
- `clear_settings_cache` fixture resets config and cache between tests

## Available test files
| File | What it covers |
|---|---|
| `test_health.py` | Health check, DB health endpoints |
| `test_login.py` | User login with employee_no |
| `test_api_fixes.py` | General API correctness |
| `test_inventory_transaction.py` | Inventory flow + stock transactions |
| `test_outbound_stock_check.py` | Outbound order stock validation |
| `test_replenishment_auto_assignment.py` | Auto warehouse assignment for replenishment |
| `test_recommendation.py` | AI recommendation generation |
| `test_llm_router.py` | LLM provider routing (DeepSeek/Ollama/rule) |
| `test_example_data_load.py` | Example data import integrity |
| `test_distributed_reconciliation.py` | Distributed reconciliation logic |
