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
    "import_export",                 # 【!!! 必须添加这一行 !!!】这是核心库
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
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

# 密码验证器
AUTH_PASSWORD_VALIDATORS = [
    {
        # 验证密码是否与用户信息（如用户名）太相似
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # 验证密码长度（默认最少8位）
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        # 验证是否是常见密码（如 123456, password, qwerty 等）
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # 验证是否全为数字
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 登录成功后，直接跳转到首页（也就是人脸搜索页）
LOGIN_REDIRECT_URL = '/'

# 退出登录后，跳转到登录页
LOGOUT_REDIRECT_URL = '/admin/login/'