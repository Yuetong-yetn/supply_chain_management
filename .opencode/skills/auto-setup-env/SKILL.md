---
name: auto-setup-env
description: 需要一键安装配置系统所需的环境、依赖包、数据库，启动系统，以及错误的诊断与修复方案，或者有系统启动需求时使用。
---

## What I do

- 搭建运行环境：创建 Python 3.10 + 虚拟环境（`.venv`）→ 安装 `backend/requirements.txt` 中的依赖，从 `.env.example` 复制环境变量配置文件
- 初始化数据库：运行 `scripts/init_db.py --rebuild` 重建所有表并插入默认用户，生成示例数据 JSON 文件，导入示例数据到数据库
- 创建新终端，在新终端中启动系统：`uvicorn main:app --reload --port 8000`，在原终端返回运行结果
- 访问 `/api/health`、`/api/system/agents`、`/docs`、`/ui/`
- 如有错误，依据终端报错模块进行诊断并修复

## When to use me

首次运行项目需要搭建开发环境、或环境出现问题导致系统无法正常启动时使用。
若所提出需求不明确，可再次向用户提问明确需求。
