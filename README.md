# LLM Price Hub (大模型比价平台)


**版本**: v0.0.1

## 项目简介
一个公开的大模型服务商比价与信誉查询平台，允许用户查找特定模型的全网最低价，并通过社区评价和客观监控数据避坑。

## 技术栈
- **Backend**: FastAPI + SQLModel
- **Frontend**: Vue 3 + Element Plus + TailwindCSS
- **Database**: MySQL 8.0

## 快速开始

### 环境变量配置

复制 `.env.example` 到 `.env` 并配置以下变量：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT 密钥（生产环境必须更改）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（分钟）
- `ENV`: 环境类型（development/production）
- `ALLOWED_ORIGINS`: CORS 允许的源（生产环境应设置具体域名）

### 启动服务

```bash
# 启动所有服务
docker-compose up -d
```

## 目录结构
- `backend/`: FastAPI 后端代码
- `frontend/`: Vue 3 前端代码
