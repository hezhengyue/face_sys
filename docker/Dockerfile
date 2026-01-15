FROM python:3.12

WORKDIR /app

# 直接安装系统依赖（跳过无效的 apt 源修改）
# 注：Python 3.12 镜像的 apt 源默认已优化，无需手动改
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ========== 核心：pip 永久配置国内源（清华源） ==========
RUN mkdir -p ~/.pip && \
    echo "[global]" > ~/.pip/pip.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> ~/.pip/pip.conf && \
    echo "trusted-host = pypi.tuna.tsinghua.edu.cn" >> ~/.pip/pip.conf

# 安装 Python 依赖（自动使用清华源，大幅提速）
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# 复制代码
COPY . .

# 创建日志文件夹
RUN mkdir -p logs/face logs/import logs/system logs/user

# 默认启动命令
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "--timeout", "300"]