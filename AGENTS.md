# AGENTS.md — Supply Chain Multi-Agent System

## What this project is

A **single FastAPI process** that at startup registers 13 Agent modules via `SisyphusOrchestrator`. Each Agent owns its models, handler, router, and event subscriptions. Cross-Agent calls go through an in-process synchronous `EventBus` — **no message queue, no microservices**.

**Entrypoint**: `backend/main.py`
**Agent registration**: `backend/agents/__init__.py` → `register_all_agents(orchestrator)`
**Route-to-Agent map**: `backend/kernel/sisyphus/gateway.py`

## Directory layout (backend)

```
backend/
├── kernel/common/       # Shared infra: config, db, auth, llm_service, event bus, exceptions
├── kernel/sisyphus/      # Orchestrator + gateway + workflow
├── agents/{agent}/       # 13 agents, each with agent.py, router.py, handler.py, models.py, events.py
├── scripts/              # init_db, generate/load example data — run from project ROOT, not backend/
├── main.py
└── .env                  # DATABASE_URL, LLM_PROVIDER, AUTH_SECRET_KEY
```

## Startup commands (all from backend/)

```powershell
backend/.venv/Scripts/Activate.ps1
pip install -r requirements.txt

# DB init scripts run from PROJECT ROOT (not backend/):
# cd ..
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py

# Start dev server (from backend/):
cd backend
uvicorn main:app --reload --port 8000
```

**Gotcha**: `init_db.py` etc. reference `backend/` paths — they MUST run from the project root directory, not from `backend/`.

## Architecture rules

### Agent isolation
- Agent A's `handler.py` MUST NOT import Agent B's `handler.py` directly.
- Cross-Agent data access goes through `kernel/common/query_service.py` (lazy imports inside functions).
- Cross-Agent **logic** goes through `event_bus.publish(Event(...))`.
- Exception: `recommendation_agent` still directly imports other agents' models (historical, not yet fully isolated).
- All `from agents.other_agent.models import ...` must be inside a function (lazy import), never at module top level.

### Each Agent must implement (see `kernel/common/base_agent.py`)
- `info` → `AgentInfo(name, description, owns_tables)`
- `register_routes()` → list of `APIRouter`
- `register_subscriptions()` → `{event_type: handler}` dict

### Event bus behavior
- Synchronous, in-process. All subscribers run before `publish()` returns.
- If a subscriber fails, other subscribers still run; the publisher is not affected (error logged, not raised).
- Events carry `_db` key when the subscriber needs to reuse the publisher's DB session.

### All API responses
```json
{"success": true, "message": "ok", "data": ...}
{"success": false, "message": "error string", "data": null}
```
Errors are handled by exception handlers in `main.py`: `BusinessException → 400`, `RequestValidationError → 422`, `IntegrityError → 400`, unhandled → 500.

## 13 Agents at a glance

| Route prefix | Agent | Owned tables | Key events |
|---|---|---|---|
| `/api/users` | user_agent | users | publishes `user.logged_in` |
| `/api/products`, `/api/categories` | product_agent | products, categories | publishes `product.created` |
| `/api/suppliers` | supplier_agent | suppliers, supplier_products, supplier_score_snapshots | publishes `supplier.scored` |
| `/api/purchase-orders`, `/api/inbound-orders` | procurement_agent | purchase_orders, inbound_orders | publishes `procurement.inbound.completed` |
| `/api/inventory` | inventory_agent | inventory | subscribes to inbound/shipped/signed events |
| `/api/warehouses` | warehouse_agent | warehouses | — |
| `/api/stores` | store_agent | stores | — |
| `/api/replenishment-requests`, `/api/outbound-orders` | fulfillment_agent | replenishment_requests, outbound_orders, outbound_items | publishes `outbound.shipped`, `outbound.signed` |
| `/api/transactions` | transaction_agent | stock_transactions | subscribes to stock changes |
| `/api/analytics` | analytics_agent | (read-only via query_service) | — |
| `/api/recommendations` | recommendation_agent | ai_recommendations, monthly_sales_facts, promotions | — |
| `/api/health`, `/api/llm`, `/api/example` | monitoring_agent | none | — |
| `/api/analysis` | analysis_agent | inventory_warning_analyses, restock_risk_analyses | subscribes to stock changes (LLM analysis) |

Note: `analysis_agent` is the 13th agent, added after the original 12.

## LLM Integration (DeepSeek)

All external LLM calls go through `kernel/common/llm_service.py`. There are **4 entry points**:

| Method | Called by | Purpose |
|---|---|---|
| `enhance_reason()` | `recommendation_agent/handler.py` — `_batch_evaluate_risk_and_enhance()` | Generate natural-language replenishment reason text + compute risk level via `evaluate_restock_risk()` |
| `evaluate_supplier()` | `supplier_agent/handler.py` — `recalculate_scores()` | Score suppliers 0-100 |
| `analyze_inventory_risk()` | `analysis_agent/handler.py` — `_run_inventory_warning_analysis()` | Classify stock as critical_stockout/stockout/overstock/none |
| `evaluate_restock_risk()` | `analysis_agent/handler.py` — `_run_restock_risk_analysis()` | Classify restock risk as high/medium/low |

- `DeepseekProvider` uses `httpx.Client` with connection pooling (reused across calls, not per-request).
- All calls use `ThreadPoolExecutor(max_workers=10)` for concurrency (in `recommendation_agent` and `supplier_agent`).
- Failure fallback: `RuleProvider` (hardcoded thresholds) — no external dependency required.
- Config: `LLM_PROVIDER=deepseek`, `DEEPSEEK_API_KEY_FILE=./.deepseek_api_key`
- Check status: `GET /api/llm/status` returns `{"provider":"deepseek","available":true}`

### Key LLM latency facts
- Single DeepSeek call: ~1.5-3s
- Supplier scoring (12 suppliers, concurrent): ~8s
- Generate recommendations (200 recs, concurrent 10 workers): ~30s
- **Frontend fetch timeout** for these long operations is set in `frontend/api.js` `TIMEOUTS` map: generate=120s, recalculate scores=60s, default=15s.

## Database

- Default: SQLite at `backend/schema/supply_chain.db`
- Optional: OceanBase/MySQL via `DATABASE_URL=mysql+pymysql://...`
- Auto-fallback: if MySQL connection fails at import time, SQLite is used.
- Table creation: `Base.metadata.create_all()` on startup (no Alembic).
- Scripts use the same SQLAlchemy models as the app — they must load all models before creating tables.

## Authentication

- JWT Bearer tokens. Login accepts `employee_no` (e.g. `A1001`) or `username` (e.g. `admin`) in the `username` field.
- Demo accounts: `admin`/`admin123`, `buyer`/`buyer123`, `warehouse`/`warehouse123`, `store`/`store123`, `manager`/`manager123`
- All business routes require `Depends(get_current_user)`.
- Verification codes are returned in plaintext in dev mode (`APP_ENV=dev`).

## Frontend

- Static files in `frontend/`, served by FastAPI at `/ui/`.
- No build step. No npm. Plain HTML + JS + ECharts.
- All backend calls through `frontend/api.js` — single `request()` function with fetch + AbortController.
- `frontend/app.js` owns all UI logic (DOM manipulation, event handlers, ECharts rendering).

## Key gotchas and conventions

1. **Scripts run from project root, server runs from `backend/`**. The two use different working directories.
2. **`generate_no("OUT", ...)` uses `OutboundOrder` count** (not `ReplenishmentRequest` count) — a historical bug was fixed to use the right table per prefix.
3. **`_batch_enhance_reasons` was renamed to `_batch_evaluate_risk_and_enhance`** — now also calls `evaluate_restock_risk` to compute risk level from LLM.
4. **`analysis_agent.handler._run_restock_risk_analysis` imports `generate_recommendations` from `recommendation_agent.handler`** at function level — a cross-agent direct import that hasn't been refactored yet.
5. **`InventoryWarning` vs `Inventory`**: `inventory_agent/handler.py:get_warnings()` does rule-based threshold check for quick in-memory warnings. `analysis_agent` does LLM-based analysis stored in `inventory_warning_analyses` table. They coexist for different purposes.
6. **`__frontend_version__`** in `backend/main.py:5` — increment this string to force browsers to re-fetch static frontend files.
7. **`.deepseek_api_key`** in `backend/` is git-ignored (listed in `.gitignore`). Never hardcode API keys.
