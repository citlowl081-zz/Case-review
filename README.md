# 临床试验文档智能审核 RAG Agent 系统

基于 LangChain 的企业级 RAG 知识库问答系统，面向医疗/临床试验文件智能审核场景。

## 功能概览

### 🔐 用户系统
- 注册/登录/修改密码 (JWT + bcrypt)
- 角色权限：管理员 (admin) / 普通用户 (user)
- 默认管理员: `admin` / `123456`

### 📚 知识库管理 (管理员)
- 文档上传 (PDF/Word/TXT/Markdown/CSV/Excel)
- 文档分类：研究方案、药物管理手册、病例记录、检查报告、AE表等
- 文档删除 (同步删除向量数据)
- 处理状态追踪 (上传中→解析中→向量化中→已完成)

### 💬 知识库问答
- 流式 SSE 输出 (打字机效果)
- 引用来源卡片 (文档名 + 原文片段)
- 多轮对话记忆
- 点赞/点踩反馈
- 复制答案

### 📝 会话管理
- 创建/重命名/删除会话
- 用户隔离 (互不可见)
- 历史对话持久化

### 🔍 智能审核 (管理员)
- 访视时间窗审核
- 纳排标准审核
- AE 时间逻辑审核
- 文档一致性审核

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design 5 |
| 后端 | FastAPI (Python) |
| AI 编排 | LangChain + LangGraph |
| LLM | 阿里云百炼 DashScope (Qwen-Max) |
| Embedding | DashScope text-embedding-v2 |
| 向量数据库 | ChromaDB |
| 关系数据库 | PostgreSQL 15 |
| 缓存 | Redis |
| 异步任务 | Celery |
| 认证 | JWT + bcrypt |

## 快速开始

### 1. 克隆并配置环境

```bash
# 运行环境搭建脚本 (macOS)
chmod +x setup.sh
./setup.sh
```

或手动安装：

```bash
# 安装依赖
brew install postgresql@15 redis node@20

# 启动服务
brew services start postgresql@15
brew services start redis

# 创建数据库
createdb langchain_rag

# Python 虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY
```

### 3. 启动

```bash
# 终端1: 后端 API
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端2: Celery Worker (文档处理)
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# 终端3: 前端开发服务器
cd frontend
npm run dev
```

### 4. 访问

- 前端: http://localhost:5173
- API 文档: http://localhost:8000/docs
- 默认管理员: admin / 123456

## 项目结构

```
langchainRAG/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由 (auth, chat, knowledge, session, user)
│   │   ├── core/         # 配置、安全、数据库、依赖注入
│   │   ├── models/       # SQLAlchemy 数据模型
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── rag/          # RAG 引擎 (loader, chunker, embeddings, retriever, chain)
│   │   ├── services/     # 业务逻辑层
│   │   ├── middleware/   # 限流、日志中间件
│   │   └── tasks/        # Celery 后台任务
│   ├── requirements.txt
│   └── storage/docs/     # 上传文件存储
├── frontend/
│   ├── src/
│   │   ├── pages/        # 页面组件 (Login, Chat, KnowledgeBase, Review, Settings)
│   │   ├── components/   # 公共组件 (Layout, ThemeToggle, StreamText)
│   │   ├── services/     # API 调用层
│   │   ├── store/        # Zustand 状态管理
│   │   ├── hooks/        # React Hooks
│   │   └── types/        # TypeScript 类型
│   └── package.json
├── .env.example
├── setup.sh
└── README.md
```

## API 路由

```
POST   /api/auth/register              # 用户注册
POST   /api/auth/login                 # 用户登录
POST   /api/auth/change-password       # 修改密码
GET    /api/users/me                   # 当前用户信息
GET    /api/sessions                   # 会话列表
POST   /api/sessions                   # 创建会话
PATCH  /api/sessions/{id}              # 更新会话
DELETE /api/sessions/{id}              # 删除会话
GET    /api/chat/sessions/{id}/messages  # 消息列表
POST   /api/chat/sessions/{id}/stream    # SSE 流式问答
POST   /api/chat/sessions/{id}/feedback/{mid}  # 消息反馈
POST   /api/knowledge/upload           # 上传文档 (admin)
GET    /api/knowledge/documents        # 文档列表 (admin)
DELETE /api/knowledge/documents/{id}   # 删除文档 (admin)
GET    /api/knowledge/stats            # 知识库统计 (admin)
GET    /api/health                     # 健康检查
```

## License

MIT
