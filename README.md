# LLM Price Hub (大模型比价平台)


## 项目简介
一个公开的大模型服务商比价与信誉查询平台，允许用户查找特定模型的全网最低价，并通过社区评价和客观监控数据避坑。

## 技术栈
- **Backend**: FastAPI + SQLModel
- **Frontend**: Vue 3 + Element Plus + TailwindCSS
- **Database**: MySQL 8.0

## 快速开始 (开发环境)

```bash
# 启动所有服务
docker-compose up -d
```

## 部署 (生产环境)

1. 复制环境变量示例文件并修改配置：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置安全的密码和密钥
   ```

2. 使用生产环境配置启动：
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

## 目录结构
- `backend/`: FastAPI 后端代码
- `frontend/`: Vue 3 前端代码
