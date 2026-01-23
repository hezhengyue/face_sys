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
    # === 新增插件 ===
    'axes',          # 防暴力破解
    'auditlog',      # 操作审计
    # ===============

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

    # === 新增中间件 (位置很重要) ===
    # Axes 必须在 Auth 之后 (虽然主要靠 Backend，但中间件处理锁定页面)
    'axes.middleware.AxesMiddleware',
    # Auditlog 必须在 Auth 之后，以便获取 request.user
    'auditlog.middleware.AuditlogMiddleware',
    # =============================

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
        'OPTIONS': {
            'charset': 'utf8mb4',
            # 添加下面这一行，强制设置排序规则，避免默认不一致
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', default_storage_engine=INNODB, character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci",
        },
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

AUTH_PASSWORD_VALIDATORS = [
    # 检查密码是否与用户信息（如用户名）太相似
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # 检查最小长度
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    # 检查是否是常见弱密码（如 123456, password 等）
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # 检查密码是否完全由数字组成
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

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

# =========== 初始化全局日志系统 ===========
LOG_ROOT = BASE_DIR / 'logs'
LOGS_DAYS = int(os.getenv('LOGS_DAYS', 180))


# ===================== Django原生日志 (降级为控制台输出) =====================
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

# ===================== 人脸API配置 =====================

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

# 定义图标 (注意：这里要用我们刚刚改好的中文名)
SIMPLEUI_ICON = {
    '核心业务': 'far fa-bars',
    '人员档案': 'far fa-person',
    '系统用户': 'fas fa-user-shield',
    '人脸识别': 'fas fa-camera',
    

    '安全监控': 'fas fa-shield-alt',      # 对应 axes_config.verbose_name
    '锁定记录': 'fas fa-lock',            # 对应 AccessAttempt verbose_name_plural
    '登录流水': 'fas fa-list-alt',        # 对应 AccessLog verbose_name_plural
    
    '操作审计': 'fas fa-history',         # 对应 audit_config.verbose_name
    '操作日志': 'fas fa-file-signature',  # 对应 LogEntry verbose_name_plural
}

# SimpleUI自定义菜单配置
SIMPLEUI_CONFIG = {
    'system_keep': True,
    'menu_display': [
        '人脸识别', 
        '核心业务', 
        '安全监控',  # Axes
        '操作审计',  # Auditlog
        '认证和授权' # Auth
    ], 
    'dynamic': True,
    'menus': [
        {
            'name': '人脸识别',
            'icon': 'far fa-camera',
            'models': [
                {
                    'name': '开始识别',
                    'url': '/face-scan/',
                    'icon': 'fas fa-search'
                }
            ]
        },
    ]
}




# ===================== Axes (防暴力破解) 配置 =====================
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5          # 允许失败次数
AXES_RESET_ON_SUCCESS = True    
AXES_LOCKOUT_PARAMETERS = [["username","ip_address"]] # 同一个ip只锁定一个账户
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# 账号安全 (Axes 锁定处理)
# 当用户因多次登录失败被锁定时：
# 命令行解锁：
# 解锁指定用户
# docker compose exec web python manage.py axes_reset_username <用户名>
# 解锁所有用户
# docker compose exec web python manage.py axes_reset

# 后台手动解锁：
# 登录 Django Admin 后台。
# 找到 Axes -> Access attempts。
# 删除对应用户名/IP 的失败记录即可解锁。

# ===================== Auditlog (审计) 配置 =====================
# Auditlog 默认会读取 request.META['REMOTE_ADDR']
# 配合 RealIPMiddleware，IP记录将自动生效
AUDITLOG_INCLUDE_ALL_MODELS = False # 手动注册需要的模型


