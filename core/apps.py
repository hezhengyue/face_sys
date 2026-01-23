# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = '核心业务'

    def ready(self):
        # 1. 初始化日志
        from .log_utils import configure_logging
        configure_logging()

        
        # 2. 注册信号
        try:
            import core.signals
        except ImportError:
            pass

        # 3. 注册 Auditlog 审计 (新增)
        # 必须在这里注册，确保模型已加载
        try:
            from auditlog.registry import auditlog
            
            # 引入模型 (局部引入防止循环依赖)
            from .models import User, Person
            
            # 注册系统用户模型 (记录用户被创建/修改/删除的操作)
            if not auditlog.contains(User):
                auditlog.register(User)
                
            # 注册人员档案模型
            if not auditlog.contains(Person):
                auditlog.register(Person)
                
        except ImportError:
            # 防止在没有安装 auditlog 时报错 (开发环境容错)
            pass