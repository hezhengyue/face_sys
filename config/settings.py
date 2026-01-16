import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 生产环境通常由 Docker 注入环境变量，这里是为了本地开发方便
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv('SECRET_KEY', 'ZA52Py77QHBeLhGBmAwCKyFN3BQM7CHM')

def str_to_bool(val):
    return str(val).lower() in ('true', '1', 't', 'yes', 'on')

# 安全起见，生产环境默认 DEBUG=False
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))

allowed_hosts_str = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]

csrf_trusted_str = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost,http://127.0.0.1')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_str.split(',') if origin.strip()]

# === Nginx/Docker 代理设置 (关键) ===
# 告诉 Django 它是运行在反向代理(Nginx)后面的，信任 X-Forwarded-Proto 头
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 如果全程 HTTPS，建议开启下面两项；如果是 HTTP，保持 False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False


# 应用定义
INSTALLED_APPS = [
    'simpleui', 
    "import_export",                 # 导入导出
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'axes',                          # 【安全】防暴力破解
    'auditlog',                      # 【审计】数据变更记录
    'core.apps.CoreConfig',          # 核心业务
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # === 第三方中间件 (顺序很重要) ===
    'axes.middleware.AxesMiddleware',           # 1. 先拦截非法登录
    'auditlog.middleware.AuditlogMiddleware',   # 2. 再记录谁在修改数据
    'core.middleware.ExportAuditMiddleware',    # 3. 最后记录导出操作(自定义)
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# 数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'db'),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'),
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': int(os.getenv('MYSQL_PORT', 3306)),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Redis 缓存 (Axes必须)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL','redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# === Axes 防破解配置 ===
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT = 5           # 错误5次锁定
AXES_COOLOFF_TIME = 1            # 锁定1小时
AXES_LOCKOUT_STRATEGY = 'combination_user_and_ip'
AXES_RESET_ON_SUCCESS = True

# === Auditlog 审计配置 ===
AUDITLOG_INCLUDE_ALL_MODELS = False # 手动注册，保持干净

# 用户模型
AUTH_USER_MODEL = 'core.User'

# 基础配置
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
# 提示：USE_TZ=False 表示使用本地时间存储，不使用 UTC。国内项目通常这样做没问题。
USE_TZ = False 


# 静态文件目录管理
STATIC_URL = 'static/'
# STATIC_ROOT 是 collectstatic 的存放目录，也是 Nginx 读取的目录
STATIC_ROOT = BASE_DIR / 'static'

# ⚠️ 修复：增加检测，避免 assets 目录不存在时报错
STATICFILES_DIRS = []
if (BASE_DIR / 'assets').exists():
    STATICFILES_DIRS.append(BASE_DIR / 'assets')

# 媒体文件管理
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 业务变量
FACE_API_KEY = os.getenv('FACE_API_KEY')
FACE_SECRET_KEY = os.getenv('FACE_SECRET_KEY')
FACE_GROUP_ID = os.getenv('FACE_GROUP_ID')
LOGS_DAYS = int(os.getenv('LOGS_DAYS', 7))

# 上传大文件
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 登录登出跳转
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

LOG_ROOT = BASE_DIR / 'logs'

# 日志配置 (Docker下推荐输出到 console)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',  # 生产环境只打印 WARNING 以上，调试改为 INFO
    },
}

# === SimpleUI 配置 ===
SIMPLEUI_HOME_INFO = False  # 关闭首页的 SimpleUI 推广信息
SIMPLEUI_ANALYSIS = False   # 关闭统计分析
SIMPLEUI_STATIC_OFFLINE = True

SIMPLEUI_ICON = {
    'Axes': 'far fa-eye',
    'Access attempts': 'far fa-bookmark',
    'Access failures': 'far fa-bookmark',
    'Access logs': 'far fa-bookmark',
    '核心业务': 'far fa-bars',
    '人员档案': 'far fa-person',
    '人脸识别': 'fas fa-camera',
}

# 自定义菜单配置
SIMPLEUI_CONFIG = {
    'system_keep': True,
    'menu_display': ['人脸识别', '认证和授权', 'Audit log', 'Axes', '核心业务'],
    'dynamic': True,
    'menus': [
        {
            'name': '人脸识别',
            'icon': 'fas fa-camera',
            'models': [
                {
                    'name': '开始识别',
                    'url': '/face-scan/', 
                    'icon': 'fas fa-search'
                }
            ]
        }
    ]
}