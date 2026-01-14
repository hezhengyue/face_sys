import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-me')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# 应用定义
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",  # 过滤器支持
    "unfold.contrib.forms",    # 表单支持
    "unfold.contrib.import_export", # 导入导出支持(可选)

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig', # 注册核心应用
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls' # 修改点

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # 指向根目录 templates
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

WSGI_APPLICATION = 'config.wsgi.application' # 修改点

# 数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # 如果 .env 没读到，默认使用 face_db
        'NAME': os.getenv('MYSQL_DB', 'face_db'),
        # 如果 .env 没读到，默认使用 root
        'USER': os.getenv('MYSQL_USER', 'root'),
        # 如果 .env 没读到，默认使用 1234
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '1234'),
        # [关键修复] 必须有默认值 '127.0.0.1'，不能是 None
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# Redis 缓存
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL','redis://127.0.0.1:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 用户模型
AUTH_USER_MODEL = 'core.User'

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False # 关闭UTC，使用本地时间

# 静态文件
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# 媒体文件 (上传文件)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 临时文件
TEMP_ROOT = MEDIA_ROOT / 'temp'
# 日志路径
LOG_ROOT = BASE_DIR / 'logs'

# 业务配置变量
FACE_API_KEY = os.getenv('FACE_API_KEY')
FACE_SECRET_KEY = os.getenv('FACE_SECRET_KEY')
FACE_GROUP_ID = os.getenv('FACE_GROUP_ID')
LOGS_DAYS = int(os.getenv('LOGS_DAYS', 7))
REDIS_URL = os.getenv('REDIS_URL','redis://127.0.0.1:6379/0')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# [新增] Unfold 主题配置
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "人脸识别管理系统",
    "SITE_HEADER": "Face Admin",
    "SITE_URL": "/",
    # "SITE_ICON": lambda request: static("icon.svg"),  # 可以设置Logo

    # 侧边栏配置
    "SIDEBAR": {
        "show_search": True,  # 显示菜单搜索框
        "show_all_applications": False, # 不自动显示所有APP，完全自定义
        "navigation": [
            {
                "title": _("人脸业务"),
                "separator": True, # 显示分割线
                "items": [
                    {
                        "title": _("开始扫描"),
                        "icon": "center_focus_weak", # Material Icons 图标名
                        "link": reverse_lazy("face_search"), # 指向自定义视图
                    },
                    {
                        "title": _("批量导入"),
                        "icon": "upload_file",
                        "link": reverse_lazy("batch_import_page"),
                    },
                ],
            },
            {
                "title": _("数据管理"),
                "separator": True,
                "items": [
                    {
                        "title": _("人员档案"),
                        "icon": "people",
                        "link": reverse_lazy("admin:core_person_changelist"),
                    },
                    {
                        "title": _("系统用户"),
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:core_user_changelist"),
                    },
                ],
            },
        ],
    },
    # 颜色配置 (Tailwind 风格)
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
        },
    },
}