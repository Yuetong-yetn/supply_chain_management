# AGENTS.md — Supply Chain Multi-Agent System

## What this project is

A **single FastAPI process** with a **dual-layer architecture**:

- **Business layer (traditional MVC)** lives in `backend/app/`: `api/routers/*` → `services/*` → `models/*`, wired via `register_business_routes(app)`.
- **AI capability layer (Sisyphus event-driven)** lives in `backend/agents/`. Exactly **2 Agents** (`recommendation_agent`, `analysis_agent`) are registered by `SisyphusOrchestrator` and communicate over an in-process **synchronous** `EventBus`. No message queue, no microservices.

**Entrypoint**: `backend/main.py`
**Business route registration**: `backend/app/api/__init__.py` → `register_business_routes(app)`
**AI agent registration**: `backend/agents/__init__.py` → `register_ai_agents(orchestrator)`

> ⚠️ Historic AGENTS.md/README described 13 Agents all registered via Sisyphus. The business modules were since migrated to `backend/app/` as MVC. **Only 2 AI Agents are registered via Sisyphus today.** Verify against source before trusting old docs.

## Directory layout

```
Supply_Chain_Management/
├── backend/
│   ├── main.py                  # FastAPI entrypoint (registers all routes on startup)
│   ├── app/                     # Business layer (MVC)
│   │   ├── api/routers/         # HTTP boundary: validate, call Service, wrap response
│   │   ├── services/            # business rules, transactions, state flow
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # HTTP request/response schemas
│   │   └── core/                # re-exports kernel/ (keeps singletons unique)
│   ├── agents/                  # AI capability layer (Sisyphus event-driven)
│   │   ├── recommendation_agent/
│   │   └── analysis_agent/
│   ├── kernel/
│   │   ├── common/              # config, database, auth, event, llm_service, base_agent, response, exceptions, query_service
│   │   └── sisyphus/            # SisyphusOrchestrator + workflow + gateway
│   ├── schema/                  # runtime DB files (supply_chain.db, test_suite.db)
│   ├── requirements.txt         # authoritative backend deps
│   └── .env.example
├── scripts/                     # init_db, generate/load example data — run from PROJECT ROOT, not backend/
├── example/                     # generated example JSON
├── schema/                      # auto-exported schema.sql / seed.sql / supply_chain.db
├── frontend/                    # static, served at /ui, no build step
│   ├── index.html / app.js / api.js / style.css
├── docs/api_contract.md         # single authoritative API contract
└── AGENTS.md
```

## Startup commands

DB init scripts run from **project root** (they reference `backend/` paths); the server runs from `backend/`.

```powershell
# virtual env + deps (from root)
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env

# DB init — MUST run from PROJECT ROOT
python scripts\init_db.py --rebuild
python scripts\generate_example_data.py
python scripts\load_example_data.py

# dev server — run from backend/
cd backend
uvicorn main:app --reload --port 8000
```

**Gotcha**: `init_db.py` etc. reference `backend/` paths — they MUST run from the project root, not `backend/`.

## Dev commands

All commands run from `backend/` with `.venv` activated, except the scripts above.

| Action | Command |
|---|---|
| Start dev server | `uvicorn main:app --reload --port 8000` |
| Init/reset DB | (root) `python scripts/init_db.py --rebuild` |
| Run tests | `pytest` (from `backend/`) |
| Access URLs | Demo `/demo`, UI `/ui/`, API docs `/docs`, Health `/api/health`, Agents `/api/system/agents` |

## Layer rules

- **Business layer**: normal flow is `Router -> Service -> Model/Database`; `schemas/` define the HTTP boundary. Routers must NOT implement inventory deduction, replenishment approval, or other transaction rules directly. Services must NOT construct FastAPI responses or depend on frontend behavior. ORM models must NOT be accepted/returned as public API schemas.
- **AI capability layer**: an Agent is a `BaseAgent` subclass (`kernel/common/base_agent.py`) implementing `info`, `register_routes()`, `register_subscriptions()` (+ optional `on_startup`/`on_shutdown`). A `SisyphusOrchestrator.register_agent()` mounts its routers, registers event subscriptions, and records metadata.
- **Agent isolation**: cross-Agent data access goes through `kernel/common/query_service.py` (lazy imports inside functions). Cross-Agent **logic** goes through `event_bus.publish(Event(...))`. Any `from agents.other_agent...` import must be inside a function (lazy), never module top-level.
  - ⚠️ Known violation: `analysis_agent/handler.py:_run_restock_risk_analysis` still directly imports `recommendation_agent.handler.generate_recommendations` (top-level of a function). Not yet fully isolated.
- **`backend/app/core/`** currently re-exports `kernel/` (see `app/core/database.py`, `app/core/config.py`) to keep `engine/SessionLocal/get_settings` singletons unique. The business layer still references `kernel/` directly in places; the re-export is a facade. Changing a kernel symbol's signature must update both the `kernel/` def and the `app/core/` re-export.

## Event bus behavior

- Synchronous, in-process. All subscribers run before `publish()` returns.
- If a subscriber fails, other subscribers still run; the publisher is unaffected (error logged, not raised).
- Events carry a `_db` key when a subscriber should reuse the publisher's session.
- `inventory_agent`/`transaction`/`analysis` subscribe to stock change events (`inventory.stock.increased`/`decreased`, `procurement.inbound.completed`, etc.).

## All API responses

```json
{"success": true, "message": "ok", "data": ...}
{"success": false, "message": "error string", "data": null}
```

Errors handled in `backend/main.py`: `BusinessException → 400`, `RequestValidationError → 422`, `IntegrityError → 400`, unhandled → 500. `docs/api_contract.md` is the only authoritative API contract.

## Business modules (`backend/app/api/routers/`)

| Router | Tables/domain | Notes |
|---|---|---|
| `users` | users, auth | login accepts `employee_no` (e.g. `A1001`) or `username` in the `username` field |
| `products` | products, categories | publishes `product.created` |
| `suppliers` | suppliers, supplier_products, supplier_score_snapshots | LLM `evaluate_supplier()` scoring |
| `procurement` | purchase_orders, inbound_orders | publishes `procurement.inbound.completed` |
| `inventory` | inventory | warnings/summary/adjust |
| `warehouses` | warehouses | — |
| `stores` | stores | — |
| `fulfillment` | replenishment_requests, outbound_orders, outbound_items | outbound.shipped / outbound.signed |
| `transactions` | stock_transactions | subscribes to stock changes |
| `analytics` | (read-only) | dashboard/rankings |
| `monitoring` | — | /api/health, /api/llm/status |

## AI Agents (`backend/agents/`) — exactly 2, registered via Sisyphus

| Agent | Owned tables | Subscribes to | Routes |
|---|---|---|---|
| `recommendation_agent` | `ai_recommendations`, `monthly_sales_facts`, `promotions` | — | `/api/recommendations*` |
| `analysis_agent` | `inventory_warning_analyses`, `restock_risk_analyses` | `inventory.stock.increased`, `inventory.stock.decreased` | `/api/analysis*` |

`GET /api/system/agents` lists exactly these 2 agents.

## LLM integration

All external LLM calls go through `kernel/common/llm_service.py` (providers: `deepseek` / `ollama` / `rule`). Default `LLM_PROVIDER=deepseek`, falls back to `rule` when no key configured.

| Method | Called by | Purpose |
|---|---|---|
| `enhance_reason()` | recommendation_agent | natural-language replenishment reason text |
| `evaluate_restock_risk()` | recommendation_agent + analysis_agent | risk high/medium/low |
| `evaluate_supplier()` | supplier scoring (business) | score suppliers 0-100 |
| `analyze_inventory_risk()` | analysis_agent | classify stock critical_stockout/stockout/overstock/none |

- `DeepseekProvider` uses a shared `httpx.Client` connection pool.
- Concurrency via `ThreadPoolExecutor(max_workers=10)` in recommendation/supplier; `ThreadPoolExecutor(max_workers=2)` in analysis_agent's background thread.
- Failure fallback: `RuleProvider` (hardcoded thresholds) — no external dependency required.
- **Core replenishment quantity and risk thresholds are ALWAYS rule-computed; LLM only enhances text/analysis, never decides inventory business.**
- Check status: `GET /api/llm/status`.

## Database

- Default: SQLite at `backend/schema/supply_chain.db`. Auto-exported `schema/` (root) mirrors `schema.sql`/`seed.sql`.
- Optional OceanBase/MySQL via `DATABASE_URL=mysql+pymysql://...`; auto-fallback to `SQLITE_FALLBACK_URL` if the primary connection fails at import time.
- Table creation: `Base.metadata.create_all()` on startup (no Alembic).
- Scripts use the same SQLAlchemy models as the app; init loads all models before creating tables.

## Authentication

- JWT Bearer tokens via `kernel/common/auth.py` (`get_current_user` dependency). All business routes require `Depends(get_current_user)`.
- Login accepts `employee_no` (e.g. `A1001`) or `username` (e.g. `admin`) in the `username` field.
- Demo accounts: `admin`/`admin123`, `buyer`/`buyer123`, `warehouse`/`warehouse123`, `store`/`store123`, `manager`/`manager123`.
- Dev mode (`APP_ENV=dev`) returns verification codes in plaintext for course demos.

## Frontend

- Static files in `frontend/`, served by FastAPI at `/ui/`. No build step, no npm. Plain HTML + JS + ECharts.
- All backend calls through `frontend/api.js` — a single `request()` with fetch + AbortController.
- `frontend/app.js` owns all UI logic.
- `__frontend_version__` in `backend/main.py` — increment to force browsers to re-fetch static frontend files.

## Key gotchas

1. Scripts run from project root, server runs from `backend/` — different working dirs.
2. `app/core/database.py` and `app/core/config.py` are **re-export facades** over `kernel/common/`. Change the kernel definition first, then keep the facade in sync.
3. Only 2 agents are registered via Sisyphus today; the 13-agent table in old docs is stale.
4. `backend/tests/` currently contains only compiled artifacts; Python test sources are not in the tree yet.
5. `.deepseek_api_key` and `backend/.env` are git-ignored; never commit secrets.
