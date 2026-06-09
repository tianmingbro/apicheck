# API Farm Commercial

> 基于 API Farm 构建的商业化 API 聚合网关，提供多 API Key 负载均衡、配额管理、调用审计等功能。

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

## ✨ 特性

- 🔑 **统一 API 入口**：聚合多个上游 API Key（如 OpenAI、Claude 等），自动负载均衡
- 💰 **商业化支持**：套餐管理、配额限制、按量计费
- 📊 **调用审计**：完整的请求日志，用于对账和监控
- 🖥️ **CLI 工具**：方便的命令行管理工具
- 🐳 **一键部署**：通过 Docker Compose 快速启动全套服务

## 🚀 快速启动（Docker Compose）

### 前置条件

- Docker 20.10+
- Docker Compose 2.0+

### 步骤

1. 克隆项目并进入目录
   ```bash
   git clone https://github.com/your-repo/api-farm-commercial.git
   cd api-farm-commercial

2.配置环境变量（可选）
bash

cp .env.example .env
# 编辑 .env 文件，至少修改 JWT_SECRET_KEY 和 ENCRYPTION_KEY

3.启动所有服务
bash

docker-compose up -d

4.验证服务状态
bash

curl http://localhost:8080/health

5.使用 CLI 测试
bash

api-farm register admin admin123
api-farm login admin admin123
api-farm add-key sk-xxx
api-farm chat --message "Hello"

CLI 工具
安装
bash

pip install api-farm-commercial   # 或从源码安装

命令参考
命令	说明	示例
register <用户名> <密码>	注册新用户	api-farm register alice pass123
login <用户名> <密码>	登录	api-farm login alice pass123
logout	登出	api-farm logout
add-key <API Key> [--base-url]	添加上游 API Key	api-farm add-key sk-xxx
list-keys	列出当前用户的 Key	api-farm list-keys
remove-key <ID>	删除指定 Key	api-farm remove-key 1
chat --model <模型> --message <消息>	发送聊天请求	api-farm chat --model gpt-3.5-turbo --message "Hi"
服务端地址配置

    环境变量：export API_FARM_SERVER_URL=http://localhost:8080

    命令行参数：api-farm list-keys --server-url http://myserver:8080

🛠️ 开发环境运行
安装依赖
bash

pip install -e .[dev]

初始化数据库
bash

alembic upgrade head
python scripts/seed_plans.py

启动服务端
bash

uvicorn app.main:app --reload --port 8000

文档

    生产部署指南

    REST API 文档（或访问 http://localhost:8000/docs 查看 Swagger UI）