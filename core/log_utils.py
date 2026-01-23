import os
import sys
from loguru import logger
from django.conf import settings
import logging


class InterceptHandler(logging.Handler):
    """
    将标准 logging 拦截并转发到 Loguru
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def configure_logging():
    """配置统一日志系统"""
    # 从 settings 获取配置，如果没配则使用默认值
    log_root = getattr(settings, 'LOG_ROOT', 'logs')
    logs_days = getattr(settings, 'LOGS_DAYS', 180)
    
    # 自动判断日志级别：如果是 DEBUG 模式则输出 DEBUG，否则 INFO
    debug_mode = getattr(settings, 'DEBUG', False)
    level = "DEBUG" if debug_mode else "INFO"
    # 确保路径是字符串
    log_root = str(log_root)
    os.makedirs(log_root, exist_ok=True)

    logger.remove()

    # 1. 访问日志
    logger.add(
        sink=os.path.join(log_root, "access.{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=f"{logs_days} days",
        encoding="utf-8",
        format="{message}",
        filter=lambda record: record["level"].name == "INFO",
        enqueue=True,
        mode="a", 
        backtrace=True,
    )

    # 2. 错误日志
    logger.add(
        sink=os.path.join(log_root, "error.{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=f"{logs_days} days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="WARNING",
        enqueue=True,
        mode="a", 
        backtrace=True,
    )
    
    # 3. 控制台
    logger.add(sys.stdout, level=level)
    # === 拦截 Django 原生日志 ===
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

def log_business(user, ip, action, obj, detail=""):
    """
    统一业务日志写入函数
    """
    try:
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        user_str = str(user.username) if hasattr(user, 'username') else str(user)
        if user_str == 'None' or user_str == '':
            user_str = 'System/Anonymous'

        ip_str = str(ip)

        msg = f"{now} | INFO     | 用户:{user_str} | IP:{ip_str} | 动作:{action} | 对象:{obj} | 详情:{detail}"
        
        # ================= 关键修改 =================
        # 使用 .opt(depth=1) 让 Loguru 往回找一层堆栈。
        # 这样控制台显示的就不会是 log_business:xx，而是调用 log_business 的代码位置（例如 views.py:50）
        logger.opt(depth=1).info(msg)
    except Exception as e:
        # 降级处理，保证日志系统不搞崩主程序
        logger.error(f"日志记录失败: {str(e)}")

def log_system_error(msg):
    # 错误日志同样加上 depth=1，方便定位是哪里报错
    logger.opt(depth=1).error(msg)