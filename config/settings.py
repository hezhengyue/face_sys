import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

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
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '1234'),
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
USE_TZ = False 

STATIC_URL = 'static/'

# STATIC_ROOT 是 collectstatic 的存放目录，也是 Nginx 读取的目录
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
LOG_ROOT = BASE_DIR / 'logs' # 日志根目录

# 业务变量
FACE_API_KEY = os.getenv('FACE_API_KEY')
FACE_SECRET_KEY = os.getenv('FACE_SECRET_KEY')
FACE_GROUP_ID = os.getenv('FACE_GROUP_ID')
LOGS_DAYS = int(os.getenv('LOGS_DAYS', 7))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'



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
        'level': 'WARNING',  # 只在控制台打印警告及以上，业务日志走 loguru
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


