FROM python:3.12

WORKDIR /app

# 安装系统依赖 (MySQLclient 必备)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# 复制代码
COPY . .

# 创建日志文件的占位符（防止容器启动时因为没有具体日志文件报错）
# 根据你的目录结构，确保子文件夹存在
RUN mkdir -p logs/face logs/import logs/system logs/user

# 默认启动命令 (注意这里改成了 config.wsgi)
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000"]