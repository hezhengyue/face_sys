import os
import sys
from loguru import logger
from django.conf import settings

def configure_logging():
    """初始化 Loguru 日志"""
    log_root = settings.LOG_ROOT
    modules = ['face', 'user', 'system', 'import']

    for module in modules:
        os.makedirs(os.path.join(log_root, module), exist_ok=True)

    logger.remove()
    fmt = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[module]} | {message}"

    for module in modules:
        logger.add(
            sink=os.path.join(log_root, module, f"{module}.{{time:YYYY-MM-DD}}.log"),
            rotation="00:00",
            retention=f"{settings.LOGS_DAYS} days",
            encoding="utf-8",
            format=fmt,
            filter=lambda record, m=module: record["extra"].get("module") == m,
            enqueue=True,
            level="INFO"
        )
    logger.add(sys.stdout, format=fmt, colorize=True, level="INFO")

def get_client_ip(request):
    """获取 IP 工具"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# 预定义 Logger
user_logger = logger.bind(module="user")     # 记录导出、业务操作
face_logger = logger.bind(module="face")     # 记录人脸识别结果
system_logger = logger.bind(module="system") # 记录报错
import_logger = logger.bind(module="import") # 记录下载流水