#!/bin/bash
# ============================================
# Hugging Face Spaces 一键部署脚本
# ============================================
# 用法: bash deploy/huggingface/deploy.sh <space-url>
# 示例: bash deploy/huggingface/deploy.sh https://huggingface.co/spaces/yourname/agrispatial-backend
# ============================================

set -e

SPACE_URL=$1
if [ -z "$SPACE_URL" ]; then
    echo "用法: bash deploy/huggingface/deploy.sh <space-url>"
    echo "示例: bash deploy/huggingface/deploy.sh https://huggingface.co/spaces/yourname/agrispatial-backend"
    exit 1
fi

# 从 URL 提取仓库地址
REPO_URL=$(echo "$SPACE_URL" | sed 's|https://huggingface.co/spaces/|https://huggingface.co/spaces/|')
GIT_URL="https://huggingface.co/spaces/$(echo $SPACE_URL | sed 's|https://huggingface.co/spaces/||')"

echo "=== AgriSpatial AI - Hugging Face Spaces 部署 ==="
echo "目标: $GIT_URL"

# 创建临时部署目录
DEPLOY_DIR=$(mktemp -d)
echo "临时目录: $DEPLOY_DIR"

# 复制需要的文件
cp deploy/huggingface/Dockerfile "$DEPLOY_DIR/Dockerfile"
cp -r backend/app "$DEPLOY_DIR/app"
cp backend/requirements.txt "$DEPLOY_DIR/requirements.txt"
cp backend/seed_data.py "$DEPLOY_DIR/seed_data.py"

# 创建 README.md (HF Spaces 元数据)
cat > "$DEPLOY_DIR/README.md" << 'EOF'
---
title: AgriSpatial AI Backend
emoji: 🌾
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# AgriSpatial AI Backend

智慧农业平台后端 API 服务。

## API 端点

- `/api/v1/weather` - 天气数据
- `/api/v1/raster` - 栅格数据
- `/api/v1/geo` - 地理数据
- `/api/v1/carbon` - 碳排放分析
- `/docs` - API 文档 (Swagger UI)

## 环境变量

在 Space Settings 中配置:

| 变量 | 说明 |
|------|------|
| `OPENWEATHER_API_KEY` | OpenWeather API Key |
| `DEEPSEEK_API_KEY` | DeepSeek AI API Key |
| `SECRET_KEY` | JWT 密钥 (自动生成) |
| `CORS_ORIGINS` | 前端域名 |
EOF

# 初始化 git 并推送
cd "$DEPLOY_DIR"
git init
git add .
git commit -m "Deploy AgriSpatial AI to Hugging Face Spaces"
git branch -M main
git remote add origin "$GIT_URL"
echo ""
echo "=== 推送到 Hugging Face Spaces ==="
echo "如果提示输入密码，使用你的 Hugging Face Access Token"
echo "获取 Token: https://huggingface.co/settings/tokens"
echo ""
git push -u origin main --force

echo ""
echo "=== 部署完成 ==="
echo "访问: $SPACE_URL"
echo "API 文档: ${SPACE_URL}/docs"
echo ""
echo "记得在 Space Settings 中配置环境变量:"
echo "  - OPENWEATHER_API_KEY"
echo "  - DEEPSEEK_API_KEY"
echo "  - CORS_ORIGINS (你的前端域名)"

# 清理
rm -rf "$DEPLOY_DIR"
