# LLM Price Hub (大模型比价平台)



## 项目简介
一个公开的大模型服务商比价与信誉查询平台，允许用户查找特定模型的全网最低价，并通过社区评价和客观监控数据避坑。

## 主要功能
- **多模型比价**: 支持 OpenAI, Gemini, Claude 等多种模型的价格对比。
- **用户系统**: 完整的注册、登录、邮件验证和 TOTP 双因素认证 (2FA)。
- **API Key 管理**: 用户可以安全地管理自己的 API Key。
- **后台管理**: 管理员可以审核价格提交、管理用户和系统设置。
- **数据可视化**: 提供表格、卡片和图表多种展示方式。

## 技术栈
- **Backend**: FastAPI + SQLModel (Python 3.10+)
- **Frontend**: Vue 3 + Element Plus + TailwindCSS + TypeScript
- **Database**: MySQL 8.0
- **Infrastructure**: Docker & Docker Compose

## 快速开始 (开发环境)

1. 启动所有服务：
   ```bash
   docker-compose up -d --build
   ```
2. 访问前端：http://localhost:8080
3. 访问后端 API 文档：http://localhost:8000/docs

## 部署 (生产环境)

1. **配置环境变量**
   复制示例文件并修改配置：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置安全的密码、密钥和 SMTP 邮件服务器配置
   ```

2. **启动服务**
   使用生产环境配置启动：
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **验证部署**
   - 前端页面应可通过配置的端口访问。
   - 检查日志确保数据库连接正常：`docker-compose -f docker-compose.prod.yml logs -f`

## 目录结构
- `backend/`: FastAPI 后端代码
  - `app/`: 应用核心逻辑
  - `static/`: 静态文件（如上传的图片）
- `frontend/`: Vue 3 前端代码
  - `src/`: 源代码
  - `nginx.conf`: 前端 Nginx 配置文件

## 维护与贡献
请确保在提交代码前运行测试并更新相关文档。
