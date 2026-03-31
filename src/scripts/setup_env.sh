#!/bin/bash
# setup_env.sh — 一键初始化开发环境
# 用法：bash scripts/setup_env.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "=== CodeAgentCostOptimization 环境初始化 ==="

# 1. 创建 venv
if [ ! -d ".venv" ]; then
    echo "[1/4] 创建 venv..."
    python -m venv .venv
else
    echo "[1/4] venv 已存在，跳过"
fi

# 2. 激活
source .venv/bin/activate
echo "[2/4] 已激活 venv: $(which python)"

# 3. 安装依赖
echo "[3/4] 安装依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. 安装 mini-swe-agent（submodule）
if [ -d "mini-swe-agent" ]; then
    echo "[4/4] 安装 mini-swe-agent..."
    pip install -e mini-swe-agent/ -q
else
    echo "[4/4] mini-swe-agent submodule 未找到，请先运行: git submodule update --init"
fi

echo ""
echo "=== 验证安装 ==="
python scripts/quick_test.py

echo ""
echo "✅ 环境初始化完成！"
echo "激活环境：source .venv/bin/activate"
