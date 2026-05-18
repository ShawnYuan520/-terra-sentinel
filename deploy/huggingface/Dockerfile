# ============================================
# AgriSpatial AI - Hugging Face Spaces Dockerfile
# ============================================
FROM python:3.12-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    libpango1.0-dev libcairo2-dev libgdk-pixbuf-xlib-2.0-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 源码
COPY app/ ./app/
COPY seed_data.py .

# HF Spaces 默认端口
ENV PORT=7860
EXPOSE ${PORT}

# 首次启动时自动初始化数据库并填充种子数据
CMD ["sh", "-c", "python seed_data.py 2>/dev/null; uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
