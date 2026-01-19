import os
import sys
from loguru import logger
from django.conf import settings

def configure_logging():
    """配置统一日志系统"""
    log_root = settings.LOG_ROOT
    os.makedirs(log_root, exist_ok=True)

    logger.remove()

    # 1. 访问日志 (Access Log) - 文本文件保持纯净 message
    logger.add(
        sink=os.path.join(log_root, "access.{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=f"{settings.LOGS_DAYS} days",
        encoding="utf-8",
        format="{message}",
        filter=lambda record: record["level"].name == "INFO",
        enqueue=True,
        mode="a", 
        backtrace=True,
    )

    # 2. 错误日志 (Error Log)
    logger.add(
        sink=os.path.join(log_root, "error.{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=f"{settings.LOGS_DAYS} days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="WARNING",
        enqueue=True,
        mode="a", 
        backtrace=True,
    )
    
    # 3. 控制台输出 - 这里不需要改格式，Loguru默认格式很好，关键在于调用时的 depth
    logger.add(sys.stdout, level="INFO")

def log_business(user, ip, action, obj, detail=""):
    """
    统一业务日志写入函数
    """
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

def log_system_error(msg):
    # 错误日志同样加上 depth=1，方便定位是哪里报错
    logger.opt(depth=1).error(msg)


def get_client_ip(request):
    return request.META.get('REMOTE_ADDR', '0.0.0.0')