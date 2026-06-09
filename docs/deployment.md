
---

## 2. docs/deployment.md

```markdown
# 生产环境部署指南

本文档涵盖在生产环境中部署 API Farm Commercial 所需的关键配置和安全建议。

## 前置条件

- Linux 服务器（Ubuntu 20.04+ / CentOS 7+）
- Docker 20.10+ 和 Docker Compose 2.0+
- 域名（可选，但推荐）
- 有效的 SSL 证书（推荐 Let's Encrypt）

## 1. 安全配置

### 1.1 环境变量

在 `.env` 文件中务必修改以下值：

| 变量名 | 说明 | 生成方式 |
|--------|------|----------|
| `POSTGRES_PASSWORD` | 数据库密码 | 强随机字符串 |
| `JWT_SECRET_KEY` | JWT 签名密钥，至少 32 字符 | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | API Key 加密密钥（Fernet 格式） | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

**不要将 `.env` 文件提交到版本控制！**

### 1.2 使用 secrets 管理

在 Docker Swarm 或 Kubernetes 中，使用内置 secrets 功能。对于 Docker Compose，可借助 `.env` 文件，但需严格控制访问权限：

```bash
chmod 600 .env


1.3 以非 root 用户运行容器

我们的 Dockerfile 已经创建了 appuser，无需额外配置。
2. 反向代理 + HTTPS
2.1 Nginx 配置示例
nginx

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 支持 SSE 或流式响应（如需要）
        proxy_buffering off;
        proxy_cache off;
    }
}

2.2 使用 Certbot 获取证书
bash

certbot --nginx -d api.yourdomain.com

3. 日志收集
3.1 容器日志

所有应用日志输出到 stdout，由 Docker 收集。建议配置日志驱动（如 json-file 或 loki）：
yaml

services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

3.2 集中日志分析（可选）

使用 ELK 或 Grafana Loki + Promtail 收集所有容器的日志。
4. 数据库备份
4.1 自动备份脚本
bash

#!/bin/bash
# backup_db.sh
BACKUP_DIR="/backups/postgres"
mkdir -p $BACKUP_DIR
docker exec api_farm_postgres pg_dump -U api_farm api_farm | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz

4.2 定期删除旧备份
bash

find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +7 -delete

建议配置 cron 作业每天执行。
5. 健康检查与自动重启

Docker Compose 中已包含健康检查，容器异常退出时会自动重启（restart: unless-stopped）。额外建议配置外部监控（如 UptimeRobot）检测 /health 端点。
6. 性能调优
6.1 Gunicorn Worker 数量

根据 CPU 核心数调整 docker-compose.yml 中的 --workers 参数。公式：(2 * CPU_CORES) + 1。
6.2 数据库连接池

在 app/core/config.py 中可调整 SQLAlchemy 连接池大小：
python

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

6.3 Redis 连接

如果使用 Redis 进行限流或缓存，请确保 Redis 内存配置合理。

7. 故障排查
问题	检查项
服务无法启动	docker-compose logs app；检查数据库是否健康
登录后立即 401	JWT_SECRET_KEY 不一致；token 过期时间设置
配额扣减失败	检查 users 表中的 quota_limit 和 quota_used
API Key 解密失败	ENCRYPTION_KEY 在服务端必须与添加时使用的密钥相同
8. 升级指南

    拉取最新代码：git pull

    重新构建镜像：docker-compose build app

    运行数据库迁移：docker-compose run --rm app alembic upgrade head

    重启服务：docker-compose up -d

建议在升级前备份数据库。
text


---

## 3. docs/api.md

```markdown
# REST API 文档

API Farm Commercial 提供完整的 REST API，可通过 `http://localhost:8000/docs` 查看自动生成的 Swagger UI 和 OpenAPI 规范。以下为关键端点的说明。

## 基础信息

- **Base URL**：`http://your-server:8000`（根据部署环境变化）
- **认证方式**：Bearer Token（JWT），在登录后获取
- **请求与响应格式**：JSON

## 认证相关

### POST `/auth/register`

注册新用户。

**请求体**：

```json
{
  "username": "alice",
  "password": "securepassword"
}

响应（201 Created）：
json

{
  "id": 1,
  "username": "alice",
  "role": "user"
}

POST /auth/login

登录并获取 JWT。

请求：表单格式（application/x-www-form-urlencoded）
text

username=alice&password=securepassword

响应（200 OK）：
json

{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

后续请求需要在 Authorization 头携带：Bearer <access_token>。