---
name: add-api-endpoint
description: 用于新增API端点，当有需要新增功能时调用
---

## What I do

- 在新增端点前确认端点所需Agent、HTTP和URL、请求和返回的数据结构
- 判断新增端点是否需要创建新表：如需创建，调用 `/schema-conflict-check` skill 分析表冲突并设计新表，然后按 skill 输出创建 models.py；如无需创建，直接进入下一步。修改完成后检查是否正确添加唯一性和非空约束，禁止导入其它 Agent 的 models。
- 在 handler.py 中添加新增端点对应的业务逻辑函数，完成：注入参数校验，数据库操作逻辑，跨Agent事件发布（用event_bus,不可直接import agent），结果返回。如遇失败：`raise BusinessException("原因")`
- 在对应 Agent 的 router.py 中添加路由，参考已有 Agent 的 router.py 写法（如 `backend/agents/product_agent/router.py`）。遵循：Router 只做参数校验和响应包装，不实现业务规则。
- 在对应 Agent 的 `events.py` 中添加事件常量（如需），路径格式为 `backend/agents/{agent_name}/events.py`
- 若需要新增关注事件，更新对应 Agent 的 `agent.py`，路径格式为 `backend/agents/{agent_name}/agent.py`
- 新建的Agent在 agents/__init__.py 中注册  
- 若新增 API 需要关联前端，同步更新 `frontend/api.js`（统一请求封装）、`frontend/app.js`（UI 行为）、`frontend/index.html`（页面结构）等相关前端文件
- 新增/修改 API 路径、字段、状态值或响应形状后，必须同步更新 `docs/api_contract.md`（项目唯一权威 API 契约），然后依次修改 Schemas、Routers、前端代码和测试。
- 结束上述操作后：创建一个新的终端，启动服务访问 `/api/system/agents` 确认 Agent 注册正常后，同步修改 README 等说明文档。

## When to use me

在需要新增端点时使用（GET,POST等），或新建Agent时负责建立Agent所需端点。
若所提出需求不明确，可再次向用户提问明确需求。