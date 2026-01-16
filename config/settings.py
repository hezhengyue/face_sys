import os
from pathlib import Path
from dotenv import load_dotenv

# ===================== 基础路径与环境变量配置 =====================
# 项目根目录：当前配置文件所在目录的父级父级目录（config/settings.py → config/ → 项目根）
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载环境变量文件：优先读取项目根目录的 .env 文件（本地开发用，生产环境由Docker注入环境变量）
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Django 安全密钥：生产环境必须通过.env配置，此处设置默认值仅用于本地开发调试
SECRET_KEY = os.getenv('SECRET_KEY', 'ZA52Py77QHBeLhGBmAwCKyFN3BQM7CHM')

# 辅助函数：将字符串类型的布尔值（如"True"/"1"/"false"）转换为Python布尔值
def str_to_bool(val):
    return str(val).lower() in ('true', '1', 't', 'yes', 'on')

# 调试模式：生产环境默认关闭（False），可通过.env的DEBUG变量覆盖
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))

# 允许访问的主机：逗号分隔的字符串转列表，默认允许localhost和127.0.0.1，生产环境需配置域名/服务器IP
allowed_hosts_str = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]

# CSRF信任源：解决反向代理下CSRF验证失败问题，默认允许localhost/127.0.0.1的HTTP请求
csrf_trusted_str = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost,http://127.0.0.1')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_str.split(',') if origin.strip()]

# === Nginx/Docker 反向代理核心配置 ===
# 告诉Django识别反向代理传递的X-Forwarded-Proto头，正确判断请求是HTTP还是HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF Cookie安全：True表示仅在HTTPS连接下传输CSRF Cookie（HTTP环境需设为False）
CSRF_COOKIE_SECURE = False
# Session Cookie安全：True表示仅在HTTPS连接下传输Session Cookie（HTTP环境需设为False）
SESSION_COOKIE_SECURE = False


# ===================== 应用注册配置 =====================
INSTALLED_APPS = [
    'simpleui',                # 第三方Admin后台美化插件
    "import_export",           # 第三方数据导入导出插件
    
    # Django内置核心应用
    'django.contrib.admin',    # 后台管理系统
    'django.contrib.auth',     # 用户认证系统
    'django.contrib.contenttypes', # 内容类型管理
    'django.contrib.sessions', # 会话管理
    'django.contrib.messages', # 消息提示
    'django.contrib.staticfiles', # 静态文件管理
    
    'axes',                    # 第三方安全插件：防暴力破解登录
    'auditlog',                # 第三方审计插件：记录数据变更操作
    'core.apps.CoreConfig',    # 自定义核心业务应用
]

# ===================== 中间件配置（执行顺序至关重要）=====================
MIDDLEWARE = [
    # 🔥 必须放在第一个，先修正 IP
    'core.middleware.RealIPMiddleware', 
    # Django内置中间件
    'django.middleware.security.SecurityMiddleware',          # 安全相关中间件（XSS/点击劫持等）
    'django.contrib.sessions.middleware.SessionMiddleware',   # 会话管理
    'django.middleware.common.CommonMiddleware',              # 通用中间件（URL重写/内容长度等）
    'django.middleware.csrf.CsrfViewMiddleware',              # CSRF防护
    'django.contrib.auth.middleware.AuthenticationMiddleware', # 用户认证
    'django.contrib.messages.middleware.MessageMiddleware',    # 消息提示
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # 点击劫持防护
    
    # 第三方/自定义中间件（按功能优先级排序）
    'axes.middleware.AxesMiddleware',           # 1. 优先拦截非法登录尝试
    'auditlog.middleware.AuditlogMiddleware',   # 2. 记录数据变更操作
    'core.middleware.ExportAuditMiddleware',    # 3. 自定义中间件：记录数据导出操作
]

# 根URL配置文件路径：项目的URL路由入口
ROOT_URLCONF = 'config.urls'

# ===================== 模板配置 =====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates', # 使用Django默认模板引擎
        'DIRS': [BASE_DIR / 'templates'], # 自定义模板文件目录
        'APP_DIRS': True, # 自动扫描各应用下的templates目录
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',    # 调试模式上下文
                'django.template.context_processors.request',  # 把request对象传入模板
                'django.contrib.auth.context_processors.auth', # 用户认证上下文
                'django.contrib.messages.context_processors.messages', # 消息提示上下文
            ],
        },
    },
]

# WSGI应用入口：部署时Gunicorn/uWSGI会加载这个入口
WSGI_APPLICATION = 'config.wsgi.application'

# ===================== 数据库配置（MySQL）=====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # 数据库引擎：MySQL
        'NAME': os.getenv('MYSQL_DATABASE', 'db'), # 数据库名，默认db
        'USER': os.getenv('MYSQL_USER', 'root'), # 数据库用户名，默认root
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'), # 数据库密码，默认123456
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'), # 数据库主机，默认本地
        'PORT': int(os.getenv('MYSQL_PORT', 3306)), # 数据库端口，默认3306
        'OPTIONS': {
            'charset': 'utf8mb4', # 字符集：支持emoji等特殊字符
        },
    }
}

# ===================== Redis缓存配置（Axes插件必需）=====================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache', # 使用Redis作为缓存后端
        'LOCATION': os.getenv('REDIS_URL','redis://127.0.0.1:6379/1'), # Redis连接地址，默认db1
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient', # 默认客户端类
        }
    }
}

# ===================== Axes防暴力破解配置 =====================
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend', # Axes认证后端：优先拦截非法登录
    'django.contrib.auth.backends.ModelBackend', # Django默认认证后端
]
AXES_FAILURE_LIMIT = 5           # 同一用户/IP组合登录失败5次后锁定
# AXES_COOLOFF_TIME = 1            # 锁定时长（小时）：1小时后自动解锁
AXES_LOCKOUT_STRATEGY = 'combination_user_and_ip' # 锁定策略：基于用户+IP组合
AXES_RESET_ON_SUCCESS = True     # 登录成功后重置失败次数
AXES_META_PRECEDENCE = ('REMOTE_ADDR',)

# ===================== Auditlog审计日志配置 =====================
AUDITLOG_INCLUDE_ALL_MODELS = False # 不自动记录所有模型的变更，仅手动注册需要审计的模型

# ===================== 用户模型配置 =====================
AUTH_USER_MODEL = 'core.User' # 自定义用户模型：替换Django默认的User模型

# ===================== 国际化与本地化配置 =====================
LANGUAGE_CODE = 'zh-hans'     # 界面语言：简体中文
TIME_ZONE = 'Asia/Shanghai'   # 时区：上海（东八区）
USE_I18N = True               # 启用国际化
USE_TZ = False                # 不使用UTC时间，存储本地时间（国内项目推荐）

# ===================== 静态文件管理（自动创建目录）=====================
# STATICFILES_DIRS：自定义静态文件源目录（本项目暂不使用assets目录，故为空）
# STATICFILES_DIRS 是「静态文件的源目录」（Django 要收集的文件在哪里）
STATICFILES_DIRS = []

# 静态文件访问URL前缀：例如/static/css/style.css
STATIC_URL = 'static/'       
# STATIC_ROOT：collectstatic命令的输出目录，Nginx实际读取静态文件的目录
# STATIC_ROOT 是「静态文件的目标目录」（collectstatic 把文件复制到哪里）
STATIC_ROOT = BASE_DIR / 'static'
# 自动创建STATIC_ROOT目录：避免执行collectstatic时因目录不存在报错
if not STATIC_ROOT.exists():
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# ===================== 媒体文件管理（自动创建目录）=====================
MEDIA_URL = '/media/'          # 媒体文件访问URL前缀：例如/media/face/photo.jpg
MEDIA_ROOT = BASE_DIR / 'media' # 媒体文件（用户上传）的本地存储目录
# 自动创建MEDIA_ROOT目录：避免用户上传文件时因目录不存在报错
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# ===================== 日志目录与业务变量配置 =====================
LOG_ROOT = BASE_DIR / 'logs'   # 日志文件根目录（具体日志子目录在其他地方创建）

# 人脸识别API相关配置（从环境变量读取）
FACE_API_KEY = os.getenv('FACE_API_KEY')       # 人脸识别API的Key
FACE_SECRET_KEY = os.getenv('FACE_SECRET_KEY') # 人脸识别API的Secret
FACE_GROUP_ID = os.getenv('FACE_GROUP_ID')     # 人脸识别分组ID
LOGS_DAYS = int(os.getenv('LOGS_DAYS', 7))     # 日志保留天数，默认7天

# ===================== 其他基础配置 =====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' # 模型默认主键类型：BigInt自增

# 登录/登出跳转配置
LOGIN_REDIRECT_URL = '/admin/'    # 登录成功后跳转至Admin首页
LOGOUT_REDIRECT_URL = '/admin/login/' # 登出后跳转至Admin登录页

# ===================== 日志配置（适配Docker）=====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # 不禁用已存在的日志器
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler', # 输出到控制台（Docker推荐方式，便于日志收集）
        },
    },
    'root': {
        'handlers': ['console'],            # 根日志器使用console处理器
        'level': 'WARNING',                 # 日志级别：生产环境仅记录WARNING及以上，调试可改为INFO
    },
}

# ===================== SimpleUI后台美化配置 =====================
SIMPLEUI_HOME_INFO = False  # 关闭SimpleUI首页的推广信息
SIMPLEUI_ANALYSIS = False   # 关闭SimpleUI的统计分析（隐私保护）
SIMPLEUI_STATIC_OFFLINE = True # 使用离线静态文件：避免加载CDN资源
# 动态判断logo文件是否存在，存在则设置，不存在则不设置
logo_file_path = MEDIA_ROOT / 'logo.png'  # 拼接logo文件的完整本地路径
if logo_file_path.exists():
    SIMPLEUI_LOGO = '/media/logo.png'  # 文件存在时设置自定义logo

# SimpleUI图标自定义：为Admin后台模型配置图标
SIMPLEUI_ICON = {
    'Axes': 'far fa-eye',
    'Access attempts': 'far fa-bookmark',
    'Access failures': 'far fa-bookmark',
    'Access logs': 'far fa-bookmark',
    '核心业务': 'far fa-bars',
    '人员档案': 'far fa-person',
    '人脸识别': 'fas fa-camera',
}

# SimpleUI自定义菜单配置
SIMPLEUI_CONFIG = {
    'system_keep': True, # 保留系统默认菜单
    'menu_display': ['人脸识别', 'Audit log', 'Axes', '核心业务'], # 显示指定菜单，隐藏'认证和授权',
    'dynamic': True,     # 启用动态菜单
    'menus': [
        {
            'name': '人脸识别', # 菜单名称
            'icon': 'fas fa-camera', # 菜单图标
            'models': [
                {
                    'name': '开始识别', # 子菜单名称
                    'url': '/face-scan/', # 子菜单跳转URL
                    'icon': 'fas fa-search' # 子菜单图标
                }
            ]
        }
    ]
}