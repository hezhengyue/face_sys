FROM python:3.12

WORKDIR /app

# 1. 安装系统底层依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 2. 配置 pip 为清华源 (加速构建)
RUN mkdir -p ~/.pip && \
    echo "[global]" > ~/.pip/pip.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> ~/.pip/pip.conf && \
    echo "trusted-host = pypi.tuna.tsinghua.edu.cn" >> ~/.pip/pip.conf

# 3. 安装 Python 依赖 (利用缓存层)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# 4. 复制代码
# (因为 .dockerignore 配置正确，这里会包含 migrations 但不包含 .env/logs)
COPY . .

# 5. 创建必要的运行时目录
RUN mkdir -p logs/django logs/nginx static media

# 6. 设置默认命令 (会被 docker-compose 覆盖，但作为备份很好)
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "4", "--timeout", "300"]