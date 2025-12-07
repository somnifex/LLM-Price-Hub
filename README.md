# LLM Price Hub (大模型比价平台)


**版本**: v0.0.1

## 项目简介
一个公开的大模型服务商比价与信誉查询平台，允许用户查找特定模型的全网最低价，并通过社区评价和客观监控数据避坑。

## 技术栈
- **Backend**: FastAPI + SQLModel
- **Frontend**: Vue 3 + Element Plus + TailwindCSS
- **Database**: MySQL 8.0

## 快速开始

```bash
# 启动所有服务
docker-compose up -d
```

## 目录结构
- `backend/`: FastAPI 后端代码
- `frontend/`: Vue 3 前端代码
- `.githooks/`: Git hooks for code quality checks

## 开发工具

### Git Hooks

项目包含了用于检测未提交更改的 Git hooks。要启用这些 hooks，请运行：

```bash
git config core.hooksPath .githooks
```

您也可以手动检查未提交的更改：

```bash
./check-uncommitted-changes.sh
```

更多信息请查看 [.githooks/README.md](.githooks/README.md)。
