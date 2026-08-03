# 供应链多智能体协同管理系统

基于 **FastAPI** 的供应链协同管理课程项目，采用**双轨架构**：

- **业务层（传统 MVC）**：`backend/app/` 下的 `Router → Service → Model`，覆盖用户、商品、供应商、采购、库存、仓库、门店、出库履约、流水、看板、监控等全部业务。
- **AI 能力层（Sisyphus 事件驱动）**：`backend/agents/` 下的 2 个 AI Agent（补货建议、LLM 自动分析），由 Sisyphus Orchestrator 注册并在进程内 Event Bus 上订阅库存变动事件。

系统仍是**单体 FastAPI 应用**，不是微服务，也没有外部消息队列。

## 当前实现概览

```text
浏览器 / API 客户端
        |
        v
FastAPI (backend/main.py)
   | 统一异常处理 + JWT 认证 + /ui 静态托管
   |
   |-- 业务层  backend/app (传统 MVC)
   |      api/routers/*  →  services/*  →  models/* (SQLAlchemy)
   |      users / products / suppliers / procurement / inventory
   |      warehouses / stores / fulfillment / transactions / analytics / monitoring
   |
   |-- AI 能力层  backend/agents (Sisyphus + EventBus)
   |      recommendation_agent  /api/recommendations  补货建议
   |      analysis_agent        /api/analysis         LLM 库存预警 + 补货风险
   |
   `-- kernel/common 共享基础设施
          config / database / auth(JWT) / event(EventBus)
          llm_service / response / exceptions / query_service / base_agent
          |
          `-- SQLAlchemy -> SQLite / MySQL(兼容 OceanBase)
```

EventBus 是**进程内同步发布/订阅**。库存变化和库存流水与业务状态在**同一请求事务**中提交；事件处理失败时请求事务回滚，避免「接口成功但库存未更新」。

## 双轨架构：业务层 vs AI 能力层

### 业务层（`backend/app/`）

11 个业务模块以传统 MVC 方式组织，通过 `app/api/__init__.py` 的 `register_business_routes(app)` 统一挂载：

| 模块 | 文件 | 主要 API |
|---|---|---|
| 用户/认证 | `users.py` | `/api/users/*` |
| 商品/品类 | `products.py` | `/api/products`、`/api/categories` |
| 供应商 | `suppliers.py` | `/api/suppliers/*` |
| 采购/入库 | `procurement.py` | `/api/purchase-orders/*`、`/api/inbound-orders/*` |
| 库存 | `inventory.py` | `/api/inventory/*` |
| 仓库 | `warehouses.py` | `/api/warehouses/*` |
| 门店 | `stores.py` | `/api/stores/*` |
| 出库履约 | `fulfillment.py` | `/api/replenishment-requests/*`、`/api/outbound-orders/*` |
| 流水 | `transactions.py` | `/api/transactions/*` |
| 看板 | `analytics.py` | `/api/analytics/*` |
| 健康监控 | `monitoring.py` | `/api/health`、`/api/llm/status` 等 |

分层规则：Router 只负责参数校验、调用 Service 并封装响应；Service 承载业务规则、事务与状态流转；ORM Model 不作为公共 API Schema 返回；`schemas/` 定义 HTTP 边界。

### AI 能力层（`backend/agents/`）

通过 `backend/agents/__init__.py` 的 `register_ai_agents(orchestrator)`，只注册 2 个 Agent：

| Agent | 拥有表 | 说明 |
|---|---|---|
| `recommendation_agent` | `ai_recommendations`, `monthly_sales_facts`, `promotions` | 规则计算补货数量，可选 LLM 增强理由文本 |
| `analysis_agent` | `inventory_warning_analyses`, `restock_risk_analyses` | 订阅库存变动事件，后台线程驱动 LLM 分析 |

`kernel/sisyphus/orchestrator.py` 的 `SisyphusOrchestrator.register_agent()` 在启动时完成：收集 Agent 元信息、挂载其路由、将事件订阅注册到全局 `event_bus`。可通过 `GET /api/system/agents` 查看已注册 Agent。

## 项目结构

```text
Supply_Chain_Management/
├── backend/
│   ├── main.py                  # FastAPI 应用入口（启动注册全部路由）
│   ├── app/                     # 业务层（传统 MVC）
│   │   ├── api/routers/         # HTTP 边界：参数校验、调 Service、封装响应
│   │   ├── services/            # 业务规则、事务、状态流转
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── schemas/             # HTTP 请求/响应 Schema
│   │   └── core/                # 转发 kernel/ 的共享基础设施（保单例唯一）
│   ├── agents/                  # AI 能力层（Sisyphus 事件驱动）
│   │   ├── recommendation_agent/
│   │   └── analysis_agent/
│   ├── kernel/
│   │   ├── common/              # config / database / auth / event / llm_service / base_agent...
│   │   └── sisyphus/            # SisyphusOrchestrator + workflow + gateway
│   ├── schema/                  # 运行时数据库文件（supply_chain.db, test_suite.db）
│   ├── requirements.txt         # 后端运行依赖
│   └── .env.example             # 环境变量示例
├── scripts/                     # 建库、生成/导入示例数据（从项目根目录运行）
├── example/                     # 生成的示例 JSON 数据
├── schema/                      # 自动导出的 schema.sql / seed.sql / supply_chain.db
├── frontend/                    # 后端直接托管的静态前端（HTML + JS + ECharts），无构建
│   ├── index.html
│   ├── app.js
│   ├── api.js                   # 所有后端请求统一入口
│   └── style.css
├── docs/
│   └── api_contract.md          # 唯一权威 API 契约
├── backend/docs/                # OceanBase 说明、架构设计文档
├── AGENTS.md                    # 开发者指引
└── README.md
```

## 环境要求

- Windows 开发环境
- 推荐 Python 3.12；当前依赖也可在支持相应 wheel 的更高版本 Python 上运行
- 无需单独安装前端依赖或执行前端构建
- 默认课程演示使用 SQLite

## 本地启动

以下命令默认从项目根目录 `Supply_Chain_Management/` 开始执行。

### 1. 创建虚拟环境并安装依赖

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

### 2. 创建环境配置

```powershell
Copy-Item backend\.env.example backend\.env
```

默认 `.env.example`：

```env
APP_ENV=dev
DATABASE_URL=sqlite:///./schema/supply_chain.db
SQLITE_FALLBACK_URL=sqlite:///./schema/supply_chain.db
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_API_KEY_FILE=./.deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
AUTH_SECRET_KEY=course-demo-change-me-with-32-plus-bytes
```

`DATABASE_URL` 的 SQLite 相对路径会被统一解析到项目根目录 `schema/supply_chain.db`，因此从根目录跑脚本、从 `backend/` 启动服务会访问同一数据库文件。未配置 DeepSeek Key 时，LLM 提供方会自动降级为规则引擎。

### 3. 初始化数据库和示例数据

这些脚本必须从**项目根目录**运行，不可从 `backend/` 运行：

```bat
python scripts\init_db.py --rebuild
python scripts\generate_example_data.py
python scripts\load_example_data.py
```

说明：

- `init_db.py --rebuild` 会删除并重建数据库，属于破坏性操作。
- `backend/schema/supply_chain.db` 是运行时数据库；`schema/`（根目录）下另有自动导出的 `schema.sql` / `seed.sql` / `supply_chain.db`。
- `generate_example_data.py` 重新生成 `example/` 下的课程演示 JSON；`load_example_data.py` 导入商品、供应商、仓库、门店、库存、订单、流水、推荐等示例数据。
- 示例用户导入支持幂等更新，不会与初始化时的预置账号发生工号冲突。

### 4. 启动后端

```bat
cd backend
uvicorn main:app --reload --port 8000
```

启动日志应显示业务路由与 AI Agent 均已注册：

```text
[System] Business routes registered (app/api/routers)
[System] 2 AI agents registered via Sisyphus. Business routes registered via app/api.
```

## 访问地址

| 功能 | 地址 |
|---|---|
| 前端演示 | http://127.0.0.1:8000/demo |
| 静态前端 | http://127.0.0.1:8000/ui/ |
| Swagger API 文档 | http://127.0.0.1:8000/docs |
| 健康检查 | http://127.0.0.1:8000/api/health |
| Agent 列表 | http://127.0.0.1:8000/api/system/agents |
| LLM 状态 | http://127.0.0.1:8000/api/llm/status |

## 演示账号

登录接口的 `username` 字段同时接受**用户名或员工工号**，例如 `admin` 和 `A1001` 都能登录同一个账号。

| 用户名 | 工号 | 密码 | 角色 |
|---|---|---|---|
| `admin` | `A1001` | `admin123` | 系统管理员 |
| `buyer` | `P1001` | `buyer123` | 采购专员 |
| `warehouse` | `W1001` | `warehouse123` | 仓库主管 |
| `store` | `S1001` | `store123` | 门店员工 |
| `manager` | `M1001` | `manager123` | 运营经理 |

开发环境下，`POST /api/users/verification-code` 会返回明文验证码便于课程演示；生产环境 `APP_ENV=prod` 不应返回明文。

## API 验证示例

健康检查：

```bat
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/system/agents
```

使用工号登录：

```bat
curl -X POST http://127.0.0.1:8000/api/users/login -H "Content-Type: application/json" -d "{\"username\":\"A1001\",\"password\":\"admin123\"}"
```

除健康检查、登录、注册、身份预览和验证码接口外，业务接口需要携带 JWT：

```bat
curl http://127.0.0.1:8000/api/products -H "Authorization: Bearer <access_token>"
curl http://127.0.0.1:8000/api/analytics/dashboard -H "Authorization: Bearer <access_token>"
curl http://127.0.0.1:8000/api/inventory/warnings -H "Authorization: Bearer <access_token>"
```

## 关键业务流程

### 采购入库

```text
入库单完成
-> procurement.inbound.completed 事件
-> 增加仓库库存（业务层）
-> inventory.stock.increased 事件
-> 创建库存流水（业务层）
-> analysis_agent 后台线程触发 LLM 预警/补货风险分析
-> 请求事务统一提交
```

### 补货与出库

```text
门店创建补货申请
-> 审核通过
-> 转换为出库单
-> 发货后扣减仓库库存并记录流水
-> 门店签收后更新状态为 signed
```

调用转出库接口时，`source_warehouse_id` 可选；未传时自动选择可用库存充足、且当前库存量较高的仓库。没有仓库满足要求时返回业务错误。

### LLM 自动分析

```text
库存变动事件触发
-> analysis_agent 订阅
-> 后台线程（ThreadPoolExecutor, max_workers=2）异步调用 LLM：
    1. 库存预警分析（critical_stockout / stockout / overstock / none）
    2. 补货风险分析（high / medium / low）
-> 结果写入 inventory_warning_analyses 和 restock_risk_analyses 表
-> 可通过 GET /api/analysis/warnings 和 GET /api/analysis/restock-risk/{store_id} 查询
```

## 数据库行为

- 默认开发数据库：SQLite，运行时文件为 `backend/schema/supply_chain.db`。
- 配置 MySQL/OceanBase URL 后优先尝试连接；连接失败时回退到 `SQLITE_FALLBACK_URL`。
- `GET /api/health/db` 可查看当前实际使用的数据库方言。
- 请求级数据库依赖在接口成功后统一 `commit()`，异常时统一 `rollback()`。
- 当前使用 `Base.metadata.create_all()` 建表，尚未接入 Alembic。

## 统一响应格式

成功响应：

```json
{ "success": true, "message": "ok", "data": {} }
```

失败响应：

```json
{ "success": false, "message": "错误信息", "data": null }
```

分页列表的 `data` 为：

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```

完整接口定义以 `docs/api_contract.md` 为准。

## LLM 配置

系统共有 4 个 LLM 调用入口，均通过 `kernel/common/llm_service.py` 的统一 Provider 抽象：

| 调用方 | 方法 | 用途 |
|---|---|---|
| `recommendation_agent` | `enhance_reason()` | 生成自然语言补货理由文本 |
| `recommendation_agent` + `analysis_agent` | `evaluate_restock_risk()` | 补货风险 high/medium/low |
| 供应商评分（业务层） | `evaluate_supplier()` | 供应商评分 0-100 |
| `analysis_agent` | `analyze_inventory_risk()` | 库存预警分类 |

**补货数量和风险阈值始终由规则逻辑计算**，LLM 只增强理由/分析文本，不决定核心库存业务。Provider 路由支持 `deepseek` / `ollama` / `rule`。LLM 失败时自动降级到规则引擎，核心业务不受影响。

未配置外部 Key 时的默认行为：`LLM_PROVIDER=deepseek` 但无 Key → 自动降级 `rule`。可用 `GET /api/llm/status` 查看实际 provider。

## 测试

```bat
cd backend
backend\.venv\Scripts\Activate.ps1
pytest -q
```

说明：

- 测试使用 `backend/schema/test_suite.db` 独立 SQLite 库。
- 测试会话会自动重建数据库并加载种子数据。
- `api_client` fixture 返回 `fastapi.testclient.TestClient(app)`。

## 当前限制

- Event Bus 是单进程内同步实现，不支持跨进程消息投递、消息持久化和失败重试。
- `analysis_agent.handler._run_restock_risk_analysis` 仍直接导入 `recommendation_agent.handler` 中的函数，尚未完全达到严格 Agent 隔离。
- `backend/app/core/` 目前是转发 `kernel/` 的浅封装，业务层尚未完全移除对 `kernel/` 的直接引用。
- 当前没有 Alembic 数据库迁移。
- `backend/tests/` 当前仅残留编译产物，源码测试文件尚未入库（见上文「测试」）。

## 安全说明

本项目是课程 Demo，已实现：

- PBKDF2-SHA256 密码哈希存储；
- JWT Bearer Token 认证；
- 密码学安全随机验证码；
- 统一业务异常和数据库异常响应；
- 至少 32 字节的演示 JWT 默认密钥。

生产部署前仍必须：

- 使用随机生成的 `AUTH_SECRET_KEY`，不要使用仓库中的演示值；
- 启用 HTTPS；
- 补充细粒度角色和权限校验；
- 将验证码接入真实短信/邮件通道，禁止返回明文；
- 使用 MySQL/OceanBase 等生产数据库并接入 Alembic。

## 参考文档

- `AGENTS.md` — 双轨架构与开发指引
- `docs/api_contract.md` — 完整 API 契约定义
- `backend/docs/` — OceanBase 说明、架构与代码逻辑说明
