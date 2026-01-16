import os
from pathlib import Path
from dotenv import load_dotenv

# ===================== 基础配置 =====================
BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv('SECRET_KEY', 'ZA52Py77QHBeLhGBmAwCKyFN3BQM7CHM')

def str_to_bool(val):
    return str(val).lower() in ('true', '1', 't', 'yes', 'on')

DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))

allowed_hosts_str = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]

csrf_trusted_str = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost,http://127.0.0.1')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_str.split(',') if origin.strip()]

# ===================== 应用注册 =====================
INSTALLED_APPS = [
    'simpleui',
    "import_export",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 本地应用
    'core.apps.CoreConfig',
]

# ===================== 中间件配置 =====================
MIDDLEWARE = [
    # 1. 修正 IP (必须在最前)
    'core.middleware.RealIPMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # 2. 导出操作审计 (记录到文件日志)
    'core.middleware.ExportAuditMiddleware',
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

# ===================== 数据库与缓存 =====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'db'),
        'USER': os.getenv('MYSQL_USER', 'db'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'),
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': int(os.getenv('MYSQL_PORT', 3306)),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ===================== 安全与会话 =====================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1200
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

AUTH_USER_MODEL = 'core.User'

# ===================== 国际化 =====================
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False

# ===================== 静态/媒体文件 =====================
STATICFILES_DIRS = []
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
if not STATIC_ROOT.exists():
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# ===================== Django原生日志 (降级为控制台输出) =====================
LOG_ROOT = BASE_DIR / 'logs/django'
LOGS_DAYS = int(os.getenv('LOGS_DAYS', 180))

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
        'level': 'WARNING',
    },
}

# ===================== 业务配置 =====================
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

FACE_API_KEY = os.getenv('FACE_API_KEY')
FACE_SECRET_KEY = os.getenv('FACE_SECRET_KEY')
FACE_GROUP_ID = os.getenv('FACE_GROUP_ID')

# ===================== SimpleUI后台美化配置 =====================
SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_STATIC_OFFLINE = True

logo_file_path = MEDIA_ROOT / 'logo.png'
if logo_file_path.exists():
    SIMPLEUI_LOGO = '/media/logo.png'

# SimpleUI图标自定义
SIMPLEUI_ICON = {
    '核心业务': 'far fa-bars',
    '人员档案': 'far fa-person',
    '人脸识别': 'fas fa-camera',
    '系统用户': 'fas fa-user-shield',
}

# SimpleUI自定义菜单配置
SIMPLEUI_CONFIG = {
    'system_keep': True,
    'menu_display': ['人脸识别', '核心业务', ], # 隐藏'认证和授权'
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