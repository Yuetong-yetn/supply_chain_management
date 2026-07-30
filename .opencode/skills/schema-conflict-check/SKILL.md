---
name: schema-conflict-check
description: 新增API端点时，分析是否需要新建数据库表、是否会与现有表冲突、如何设计新表以保证兼容性
---

## What I do

- 分析是否需要新建表：仅新增GET查询或处理已有数据时不需要新表；需要新建新的数据结构、或插入已有表会产生隐患（权限差异，或违背设计规范），需要新建表
- 检查新表的所有外键是否引用真实存在的表和列，表命名是否存在冲突，相同字段跨表命名是否一致
- 检查字段类型是否符合项目规范：String 必须指定长度；可选字段使用 `X | None` 语法；禁止使用项目未用的类型（如 `Enum`, `JSON`, `Boolean`）
- 检查新字段是否兼容现有字段：`nullable=False` 字段需有默认值或保证插入时有值；新表与现有表有级联关系时考虑 `ondelete` 设置。
- 交由project_sisyphus判断新表归属哪个 Agent，不适合任何现有Agent时考虑新建Agent
- 提供新表设计模板（参考 `backend/agents/procurement_agent/models.py`），并更新对应Agent的 `owns_tables` 和 `scripts/init_db.py` 的 `MODEL_MODULES`
- 最后二次检查：表名不冲突、外键存在、字段兼容和一致、归属Agent正确

## When to use me

在新增API需要存储新字段，新增功能需要新建表，或修改已有表结构时使用。
如果不确定是否需要新建表，或担心新设计与现有数据库冲突。
若所提出需求不明确，可再次向用户提问明确需求。
