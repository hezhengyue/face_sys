# core/apps.py
from django.apps import AppConfig
from django.apps import apps

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

        # =========================================================
        # 4. 【核心代码】汉化第三方 APP 和 模型(子菜单)
        # =========================================================
        self.rename_axes_app()
        self.rename_auditlog_app()

    def rename_axes_app(self):
        """汉化 Axes (用户锁定与访问日志)"""
        try:
            # 1. 修改一级菜单 (APP名称)
            axes_config = apps.get_app_config('axes')
            axes_config.verbose_name = '安全监控' # 左侧一级菜单名

            # 2. 修改子菜单 (Model名称)
            from axes.models import AccessAttempt, AccessLog, AccessFailureLog
            
            # AccessAttempt: 正在被锁定的IP尝试
            AccessAttempt._meta.verbose_name = "锁定记录"
            AccessAttempt._meta.verbose_name_plural = "锁定记录" # 列表页/左侧菜单显示这个
            
            # AccessLog: 所有的登录历史
            AccessLog._meta.verbose_name = "登录流水"
            AccessLog._meta.verbose_name_plural = "登录流水"

            # AccessLog: 所有的登录历史
            AccessFailureLog._meta.verbose_name = "旧登录流水"
            AccessFailureLog._meta.verbose_name_plural = "旧登录流水"
            
        except (ImportError, LookupError):
            pass

    def rename_auditlog_app(self):
        """汉化 Auditlog (操作审计)"""
        try:
            # 1. 修改一级菜单
            audit_config = apps.get_app_config('auditlog')
            audit_config.verbose_name = '操作审计'

            # 2. 修改子菜单
            from auditlog.models import LogEntry
            
            LogEntry._meta.verbose_name = "操作日志"
            LogEntry._meta.verbose_name_plural = "操作日志" # 列表页/左侧菜单显示这个
            
        except (ImportError, LookupError):
            pass