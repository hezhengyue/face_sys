# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = '核心业务'

    def ready(self):
        # 1. 初始化日志
        try:
            from .utils import configure_logging
            configure_logging()
        except ImportError:
            pass
        
        # 2. 注册信号 (新增)
        try:
            import core.signals
        except ImportError:
            pass