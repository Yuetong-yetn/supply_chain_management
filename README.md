# Supply_Chain_Management

供应链库存协同与智能补货管理系统。项目面向数据库课程设计，包含 FastAPI 后端、SQLite 数据库 schema、示例业务数据、自动化测试，以及蓝白配色的可视化前端驾驶舱。

## 项目结构

```text
Supply_Chain_Management/
├── backend/
│   ├── app/                 # FastAPI 应用、路由、模型、服务层
│   ├── example/             # 示例数据 JSON
│   ├── schema/              # 数据库 schema 与种子 SQL
│   ├── scripts/             # 初始化、生成、导入数据脚本
│   ├── tests/               # pytest 测试
│   ├── .env.example         # 环境变量示例
│   └── requirements.txt     # 后端依赖
├── frontend/
│   ├── index.html           # 可视化驾驶舱页面
│   ├── styles.css           # 蓝白主题与响应式样式
│   └── app.js               # API 调用和图表渲染逻辑
├── .gitignore
└── README.md
```

## 已实现功能

- 基础信息管理：商品、类别、供应商、仓库、门店、用户。
- 采购与入库：采购订单、入库单、入库完成后自动增加库存并写入库存流水。
- 出库与补货：门店补货申请、审核、转出库单、发货、签收。
- 库存管理：库存查询、商品分布、库存调整、缺货和积压预警。
- 供应商评价：采购金额、供货周期、履约表现和评分排行。
- 智能补货：基于库存、安全库存、销量、供货周期、促销标记生成建议。
- 统计分析：库存排行、门店需求热度、商品周转、供应商采购排行。
- 前端可视化：运营驾驶舱、预警列表、补货建议、排行榜和热度视图。

## 本地运行

进入后端目录：

```bash
cd backend
pip install -r requirements.txt
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py
uvicorn app.main:app --reload --port 8000
```

打开页面：

- 前端驾驶舱：http://127.0.0.1:8000/ui/
- API 文档：http://127.0.0.1:8000/docs

## 测试

```bash
cd backend
python -m pytest -q
```

当前测试覆盖库存事务、出库校验、智能补货、分布式库存校验、示例数据导入和 API 修复项。

## 说明

项目默认使用 SQLite，数据库文件 `backend/schema/supply_chain.db` 属于本地运行产物，不提交到 GitHub。可通过初始化脚本和示例数据重新生成。
