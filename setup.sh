#!/bin/bash
# ==========================================
# 临床试验文档智能审核 RAG Agent — 环境搭建脚本
# 适用于 macOS (使用 Homebrew)
# ==========================================
set -e

echo "========================================"
echo "  临床试验文档智能审核 RAG Agent 环境搭建"
echo "========================================"

# --- 1. Check/Install Homebrew dependencies ---
echo ""
echo "[1/5] 检查基础依赖..."

if ! command -v brew &> /dev/null; then
    echo "请先安装 Homebrew: https://brew.sh"
    exit 1
fi

# PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "安装 PostgreSQL..."
    brew install postgresql@15
fi

# Redis
if ! command -v redis-server &> /dev/null; then
    echo "安装 Redis..."
    brew install redis
fi

# Node.js
if ! command -v node &> /dev/null; then
    echo "安装 Node.js..."
    brew install node@20
fi

echo "基础依赖检查完成 ✓"

# --- 2. Start services ---
echo ""
echo "[2/5] 启动 PostgreSQL 和 Redis..."

brew services start postgresql@15 2>/dev/null || echo "PostgreSQL 已在运行"
brew services start redis 2>/dev/null || echo "Redis 已在运行"

sleep 2  # Wait for services to be ready

# --- 3. Create database ---
echo ""
echo "[3/5] 创建数据库..."

if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw langchain_rag; then
    echo "数据库 langchain_rag 已存在"
else
    createdb langchain_rag
    echo "数据库 langchain_rag 创建成功 ✓"
fi

# --- 4. Python environment ---
echo ""
echo "[4/5] 安装 Python 依赖..."

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Python 虚拟环境创建成功 ✓"
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
echo "Python 依赖安装完成 ✓"

# --- 5. Setup env file ---
echo ""
echo "[5/5] 配置环境变量..."

cd "$(dirname "$0")"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env 文件已创建，请编辑填写 DASHSCOPE_API_KEY"
fi

# --- 6. Frontend ---
echo ""
echo "安装前端依赖..."
cd frontend
npm install
echo "前端依赖安装完成 ✓"

echo ""
echo "========================================"
echo "  环境搭建完成！"
echo ""
echo "  下一步："
echo "  1. 编辑 .env 文件，填入 DASHSCOPE_API_KEY"
echo "  2. 终端1: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  3. 终端2: cd backend && source venv/bin/activate && celery -A app.tasks.celery_app worker --loglevel=info"
echo "  4. 终端3: cd frontend && npm run dev"
echo ""
echo "  默认管理员: admin / 123456"
echo "========================================"
