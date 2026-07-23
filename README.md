# Supply Chain Multi-Agent System

基于 **FastAPI + Sisyphus Orchestrator + 12 个领域 Agent + 进程内 Event Bus** 的供应链协同管理课程项目。

系统仍是一个单体 FastAPI 应用，不是微服务。Sisyphus 在应用启动时注册全部 Agent、挂载路由并连接事件订阅；各领域 Agent 分别维护自己的模型、业务处理器和 API。

## 当前实现概览

```text
浏览器 / API 客户端
        |
        v
FastAPI + Sisyphus Orchestrator
        |
        +-- 注册并挂载 12 个领域 Agent
        |
        +-- 进程内同步 Event Bus
        |      采购入库完成 -> 库存增加 -> 库存流水
        |      出库发货     -> 仓库库存减少 -> 库存流水
        |      门店签收     -> 门店库存增加 -> 库存流水
        |
        +-- SQLAlchemy -> SQLite / MySQL / OceanBase
```

Event Bus 当前是**进程内同步发布/订阅**，不是外部消息队列。业务事件与发起请求复用同一个 SQLAlchemy Session，因此库存变化和库存流水会与业务状态在同一事务中提交；事件处理失败时请求事务会回滚，不会再出现“接口返回成功但库存没有更新”的情况。

## 12 个领域 Agent

| Agent | 主要职责 | 主要 API / 事件 |
|---|---|---|
| `user_agent` | 登录、JWT、用户注册与身份查询 | `/api/users/*` |
| `product_agent` | 商品与品类 | `/api/products`、`/api/categories` |
| `supplier_agent` | 供应商、供货商品、供应商评分 | `/api/suppliers/*` |
| `procurement_agent` | 采购单与入库单 | `/api/purchase-orders/*`、`/api/inbound-orders/*`；发布 `procurement.inbound.completed` |
| `inventory_agent` | 仓库/门店库存、库存预警与调整 | `/api/inventory/*`；订阅入库、发货、签收事件 |
| `warehouse_agent` | 仓库基础数据 | `/api/warehouses/*` |
| `store_agent` | 门店基础数据 | `/api/stores/*` |
| `fulfillment_agent` | 补货申请、审核、转出库、发货与签收 | `/api/replenishment-requests/*`、`/api/outbound-orders/*` |
| `transaction_agent` | 库存流水与追溯 | `/api/transactions/*`；订阅库存增加/减少事件 |
| `analytics_agent` | 首页看板、排行与趋势分析 | `/api/analytics/*` |
| `recommendation_agent` | 规则补货建议及可选 LLM 文本增强 | `/api/recommendations/*` |
| `monitoring_agent` | 健康检查、数据库与 LLM 状态 | `/api/health`、`/api/health/db`、`/api/llm/status` |

Sisyphus 注册状态可通过 `GET /api/system/agents` 查看，正常情况下返回 12 个 Agent。

## 项目结构

```text
supply_chain_multi_agent/
├── backend/
│   ├── agents/                  # 12 个领域 Agent
│   ├── kernel/
│   │   ├── common/              # 配置、数据库、认证、事件总线、共享查询
│   │   └── sisyphus/            # Agent 注册、路由挂载与工作流编排
│   ├── main.py                  # FastAPI 应用入口
│   ├── requirements.txt         # 后端运行依赖
│   └── .env.example             # 环境变量示例
├── frontend/                    # 后端直接托管的静态前端，无构建步骤
├── scripts/                     # 建库、生成与导入示例数据脚本
├── example/                     # 生成的示例 JSON 数据
├── schema/                      # SQLite 数据库及导出的 schema/seed 文件
├── docs/api_contract.md         # API 契约
└── README.md
```

## 环境要求

- Windows 开发环境
- 推荐 Python 3.12；当前依赖也可在支持相应 wheel 的更高版本 Python 上运行
- 无需单独安装前端依赖或执行前端构建
- 默认课程演示使用 SQLite

## 本地启动

以下命令默认从项目根目录 `supply_chain_multi_agent/` 开始执行。

### 1. 创建虚拟环境并安装依赖

```bat
python -m venv backend\.venv
backend\.venv\Scripts\activate.bat
python -m pip install -r backend\requirements.txt
```

PowerShell 激活命令为：

```powershell
backend\.venv\Scripts\Activate.ps1
```

### 2. 创建环境配置

如果使用 **CMD**：

```bat
copy backend\.env.example backend\.env
```

如果使用 **PowerShell**：

```powershell
Copy-Item backend\.env.example backend\.env
```

不要在 CMD 中使用 `Copy-Item`，它只属于 PowerShell。

默认 `.env.example` 使用：

```env
DATABASE_URL=sqlite:///./schema/supply_chain.db
SQLITE_FALLBACK_URL=sqlite:///./schema/supply_chain.db
LLM_PROVIDER=rule
AUTH_SECRET_KEY=course-demo-change-me-with-32-plus-bytes
```

SQLite 相对路径会被后端统一解析到项目根目录的 `schema/supply_chain.db`，因此从项目根目录运行脚本、从 `backend/` 启动服务时会访问同一个数据库文件。

如果你已经有旧的 `backend/.env`，请确保其中的 `AUTH_SECRET_KEY` 至少 32 字节，否则 PyJWT 会输出 `InsecureKeyLengthWarning`。生产环境必须替换为随机高强度密钥。

### 3. 初始化数据库和示例数据

这些脚本必须从**项目根目录**运行：

```bat
python scripts\init_db.py --rebuild
python scripts\generate_example_data.py
python scripts\load_example_data.py
```

说明：

- `init_db.py --rebuild` 会删除并重建当前 SQLite 数据库，属于破坏性操作。
- 初始化脚本会加载全部 Agent 模型后统一建表，确保外键引用表完整。
- `generate_example_data.py` 重新生成 `example/` 下的课程演示 JSON；已有数据文件且不需要重新生成时可以跳过。
- `load_example_data.py` 导入商品、供应商、仓库、门店、库存、订单、流水、推荐等示例数据。
- 示例用户导入支持幂等更新，不会与初始化时的预置账号发生工号冲突。

### 4. 启动后端

```bat
cd backend
uvicorn main:app --reload --port 8000
```

看到以下信息说明 12 个 Agent 已正常注册：

```text
[System] All 12 agents registered. Sisyphus orchestrator ready.
```

## 访问地址

| 功能 | 地址 |
|---|---|
| 前端演示 | http://127.0.0.1:8000/demo |
| 静态前端 | http://127.0.0.1:8000/ui/ |
| Swagger API 文档 | http://127.0.0.1:8000/docs |
| 健康检查 | http://127.0.0.1:8000/api/health |
| 数据库状态 | http://127.0.0.1:8000/api/health/db |
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

示例数据还包含两个尚未激活的员工：

| 工号 | 姓名 | 手机号 | 角色 |
|---|---|---|---|
| `S2001` | 王敏 | `13000002001` | 门店员工 |
| `W2001` | 李峰 | `13000002002` | 仓库主管 |

开发环境下，`POST /api/users/verification-code` 会返回明文验证码，便于课程演示；随后可调用 `POST /api/users/register` 激活账号。生产环境 `APP_ENV=prod` 时不应返回明文验证码。

## API 验证示例

健康检查：

```bat
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/health/db
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
-> procurement.inbound.completed
-> InventoryAgent 增加仓库库存
-> inventory.stock.increased
-> TransactionAgent 创建库存流水
-> 请求事务统一提交
```

### 补货与出库

```text
门店创建补货申请
-> 审核通过
-> 转换为出库单
-> 发货后扣减仓库库存并记录流水
-> 门店签收后增加门店库存并记录流水
```

调用转出库接口时，`source_warehouse_id` 当前为可选参数；未传入时，系统会自动选择该商品可用库存足够且当前库存量较高的仓库。没有仓库满足数量要求时返回业务错误。

## 数据库行为

- 默认开发数据库：SQLite，文件为 `schema/supply_chain.db`。
- 配置 MySQL/OceanBase URL 后会优先尝试连接；连接失败时可回退到 `SQLITE_FALLBACK_URL`。
- `GET /api/health/db` 可查看当前实际使用的数据库方言和脱敏 URL。
- FastAPI 的请求级数据库依赖会在接口成功后统一 `commit()`，异常时统一 `rollback()`。
- 当前使用 `Base.metadata.create_all()` 和初始化脚本维护表结构，尚未接入 Alembic。

## 统一响应格式

成功响应：

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```

失败响应：

```json
{
  "success": false,
  "message": "错误信息",
  "data": null
}
```

分页列表的 `data` 为：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

完整接口定义以 `docs/api_contract.md` 为准。

## LLM 配置

补货数量和风险等级由规则逻辑计算，LLM 只用于增强推荐理由文本，不决定核心库存业务。

默认配置：

```env
LLM_PROVIDER=rule
```

可选配置 DeepSeek 或 Ollama：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=<your-key>
DEEPSEEK_MODEL=deepseek-chat
```

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
```

未配置外部模型时，核心业务仍可正常运行。

## 检查

当前多智能体框架尚未补齐正式自动化测试，仓库中也不再保留临时接口自检测试。上线前需要重新建立 pytest 测试目录和关键业务用例。

如果后续补充测试，可安装 pytest 后运行：

```bat
backend\.venv\Scripts\activate.bat
python -m pip install pytest
cd backend
python -m pytest -q
```

Python 语法检查示例：

```bat
cd backend
python -m py_compile main.py
```

## 当前限制

- Event Bus 是单进程内同步实现，不支持跨进程消息投递、消息持久化和失败重试。
- 部分跨 Agent 只读查询通过 `kernel/common/query_service.py` 聚合；`recommendation_agent` 仍直接读取库存、门店和供应商模型，尚未完全达到严格 Agent 隔离。
- 当前没有 Alembic 数据库迁移。
- 当前测试覆盖有限。
- `Dockerfile` 和 `docker-compose.yml` 已提供，但目前本地脚本启动流程是已验证的主要运行方式；生产部署前需进一步校准持久化卷、数据库和密钥配置。

## 安全说明

本项目是课程 Demo，已经实现：

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
- 使用 MySQL/OceanBase 等生产数据库并接入 Alembic；
- 将进程内 Event Bus 替换为具备可靠投递能力的消息基础设施（如业务规模确有需要）。
