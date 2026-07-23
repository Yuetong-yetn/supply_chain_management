# AGENTS.md — Supply Chain Multi-Agent System

## 项目本质

Sisyphus 总指挥 + 12 个领域 Agent + Event Bus 的**运行时多智能体架构**。
每个 Agent 自包含模型、业务逻辑和 API 路由，通过事件总线异步通信。

**不是**微服务——仍然是单体 FastAPI 应用，但模块间禁止直接 import 调用。

---

## 目录结构要点

```
backend/
├── kernel/              # 核心基础设施（不可跨 Agent 调用）
│   ├── common/          # BaseAgent, EventBus, config, database, auth, cache
│   └── sisyphus/        # 编排引擎（Orchestrator, Gateway, Workflow）
├── agents/              # 12 个领域 Agent
│   ├── __init__.py      # 注册所有 Agent 的入口
│   └── {agent}/
│       ├── agent.py     # 继承 BaseAgent，声明元信息
│       ├── events.py    # 事件常量 + 订阅映射
│       ├── router.py    # FastAPI APIRouter（只做参数校验）
│       ├── handler.py   # 业务逻辑
│       └── models.py    # SQLAlchemy 模型
├── main.py              # 入口：启动时注册所有 Agent → 挂载路由
└── .env.example
```

---

## 关键命令

```powershell
# 所有命令在 backend/ 下执行
cd backend

# 首次启动
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env

# 数据库初始化（⚠️ 见下方 gotcha）
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py

# 启动
uvicorn main:app --reload --port 8000

# 验证
curl http://127.0.0.1:8000/api/system/agents   # 应返回 12 个 Agent
curl http://127.0.0.1:8000/api/health            # 健康检查
```

---

## 架构规则

### Agent 边界（重要）
- **禁止** Agent A 的 handler.py 直接 import Agent B 的 handler.py
- 跨 Agent 协作必须通过 **Event Bus**：`event_bus.publish(Event(...))`
- **例外**（当前代码中的不一致）：analytics_agent 和 recommendation_agent 直接 import 了其他 Agent 的 models——这是违反规则的，需要重构为只读 API 调用

### 事件流（核心业务流程）
```
procurement.inbound.completed
  → inventory_agent: increase_stock()  发布 inventory.stock.increased
  → transaction_agent: 记录流水（当前未实现事件回调）

fulfillment.outbound.shipped
  → inventory_agent: decrease_stock()  发布 inventory.stock.decreased
  → transaction_agent: 记录流水

fulfillment.outbound.signed
  → inventory_agent: increase_store_stock()
```

### 响应格式
```python
# 所有 API 返回同一格式
{"success": True, "message": "ok", "data": ...}
# 分页列表
{"success": True, "message": "ok", "data": {"items": [...], "total": N, "page": P, "page_size": S}}
# 错误
{"success": False, "message": "错误信息", "data": None}
```

### 错误处理
- 业务异常：`raise BusinessException("消息", status_code)`
- 框架自动处理：BusinessException → 400, RequestValidationError → 422, IntegrityError → 400

---

## Agent 映射

| 路由前缀 | Agent | 拥有表 | 关键事件 |
|---------|-------|--------|---------|
| /api/users | user_agent | users | 发布: user.logged_in |
| /api/products, /api/categories | product_agent | products, categories | 发布: product.created |
| /api/suppliers | supplier_agent | suppliers, supplier_products, supplier_score_snapshots | 评分公式见 handler |
| /api/purchase-orders, /api/inbound-orders | procurement_agent | purchase_orders, inbound_orders | 发布: procurement.inbound.completed |
| /api/inventory | inventory_agent | inventory | 订阅: inbound.completed, outbound.shipped/signed |
| /api/warehouses | warehouse_agent | warehouses | — |
| /api/stores | store_agent | stores | — |
| /api/outbound-orders, /api/replenishment-requests | fulfillment_agent | replenishment_requests, outbound_orders | 发布: outbound.shipped/signed |
| /api/transactions | transaction_agent | stock_transactions | 订阅: stock.increased/decreased |
| /api/analytics | analytics_agent | 无（只读） | 跨 Agent import models（⚠须重构） |
| /api/recommendations | recommendation_agent | ai_recommendations, monthly_sales_facts | 推荐算法见 handler |
| /api/health, /api/llm | monitoring_agent | 无 | — |

---

## 已知问题 / 修复记录

### ✅ 已修复

1. **认证系统修复**
   - `_extract_token()` 已替换为 FastAPI `HTTPBearer` 自动提取 Bearer Token
   - 所有业务路由已添加 `Depends(get_current_user)` 认证保护
   - 登录接口使用 `verify_password()` 进行 PBKDF2-SHA256 哈希验证
   - 验证码使用 `secrets.randbelow()` 生成，已哈希后存储

2. **scripts/*.py 的 import 路径已修复**
   - 所有脚本现在使用 `from kernel.common.config`、`from kernel.common.database` 等正确路径
   - 已创建 `kernel/common/example_data_service.py` 替代原 `app.services.example_data_service`

3. **analytics_agent & monitoring_agent 跨 Agent import 已修复**
   - 已创建 `kernel/common/query_service.py` 共享查询层
   - 两个 Agent 的 router.py 不再直接 import 其他 Agent 的 models

4. **inventory_agent 事件回调已实现**
   - `_handle()` 现在调用 `increase_stock()` / `decrease_stock()` 实际处理事件
   - `transaction_agent.on_stock_changed()` 现在创建 `StockTransaction` 记录

5. **密码哈希修复**
   - 创建 `kernel/common/hash_utils.py`，使用 PBKDF2-SHA256
   - 与 `schema/seed.sql` 中的哈希格式兼容

6. **基础设施添加**
   - `.gitignore`、`pyproject.toml`、Dockerfile、docker-compose.yml
   - `tests/conftest.py` 测试基础设施

### 📋 仍待处理

- **数据库迁移**：当前使用 `Base.metadata.create_all()`，生产环境需使用 Alembic
- **前端认证集成**：`frontend/api.js` 需要在请求头添加 `Authorization: Bearer <token>`

---

## 新增 Agent 的步骤

```python
# 1. 在 backend/agents/ 下新建目录 agent_xxx/
# 2. 创建 5 个文件（严格遵循以下 import 规则）
# 3. 在 agents/__init__.py 中加入 import 和实例化
# 4. 启动后访问 /api/system/agents 确认注册成功

# import 规则：
#   handler.py → from kernel.common.{database,exceptions,event}
#   handler.py → 可 from .models, from .events
#   handler.py → 不可 from agents.other_agent.handler
#   router.py  → 从 .handler import 函数
#   models.py  → 从 kernel.common.database import Base
```

---

## 参考资料

- `backend/kernel/sisyphus/gateway.py` — API 路径到 Agent 的映射表
- `backend/kernel/common/event.py` — Event/EventBus 定义
- `backend/kernel/common/base_agent.py` — BaseAgent 抽象类
- `.opencode/agents/*.md` — 每个 Agent 的开发期 AI 辅助配置
