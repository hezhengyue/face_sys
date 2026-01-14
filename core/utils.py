import os
import sys
from loguru import logger
from django.conf import settings

def configure_logging():
    log_root = settings.LOG_ROOT
    for module in ['face', 'user', 'system', 'import']:
        os.makedirs(os.path.join(log_root, module), exist_ok=True)

    logger.remove()
    fmt = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[module]} | {message}"

    for module in ['face', 'user', 'system', 'import']:
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
    logger.add(sys.stdout, format=fmt, colorize=True)

user_logger = logger.bind(module="user")
face_logger = logger.bind(module="face")
system_logger = logger.bind(module="system")
import_logger = logger.bind(module="import")