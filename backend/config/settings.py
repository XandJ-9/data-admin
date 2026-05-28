import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.db.models import F

from .env import DATABASE_CONFIG

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(name, default=None):
    value = os.environ.get(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(',') if item.strip()]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

DEFAULT_DEV_SECRET_KEY = 'django-insecure-egt!&y34$i(mnlz!k-d*4ba)ng$6+vn9(@bm^c)lxe530te35q'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', DEFAULT_DEV_SECRET_KEY)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', ['*'] if DEBUG else [])

if not DEBUG:
    if SECRET_KEY == DEFAULT_DEV_SECRET_KEY:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set when DJANGO_DEBUG=false')
    if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must be set to explicit hosts when DJANGO_DEBUG=false')


# Application definition

INSTALLED_APPS = [
    'daphne',  # ASGI server for WebSocket support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'captcha',
    'channels',  # WebSocket support
    'apps.system',
    'apps.monitor',
    'apps.dataasset',  # 数据资产管理模块
    'apps.datadev',  # 数据开发模块
    'apps.dataintegration',  # 数据集成模块
    'apps.datasource',  # 数据源管理模块
    'apps.dataservice',  # 数据服务模块
    'apps.datatask',  # 任务运维模块
    'apps.terminal',    # Web Terminal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.monitor.middleware.OperLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 指定模板文件位置
        'DIRS': [BASE_DIR /'dist'],
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
ASGI_APPLICATION = 'config.asgi.application'

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': os.environ.get('DJANGO_CHANNEL_LAYER_BACKEND', 'channels.layers.InMemoryChannelLayer')
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASE_ENGINE = os.environ.get('DJANGO_DATABASE_ENGINE', DATABASE_CONFIG['ENGINE'])
if DATABASE_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DATABASE_ENGINE,
            'NAME': os.environ.get('DJANGO_DATABASE_NAME', BASE_DIR / 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DATABASE_ENGINE,
            'NAME': os.environ.get('DJANGO_DATABASE_NAME', DATABASE_CONFIG['NAME']),
            'USER': os.environ.get('DJANGO_DATABASE_USER', DATABASE_CONFIG['USER']),
            'PASSWORD': os.environ.get('DJANGO_DATABASE_PASSWORD', DATABASE_CONFIG['PASSWORD']),
            'HOST': os.environ.get('DJANGO_DATABASE_HOST', DATABASE_CONFIG['HOST']),
            'PORT': os.environ.get('DJANGO_DATABASE_PORT', DATABASE_CONFIG['PORT']),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# 静态文件路径的前缀对应前端项目指定的baseUrl,即VITE_APP_BASE_URL
# STATIC_URL = VITE_APP_BASE_URL + 'static/'
STATIC_URL = '/static/'

STATIC_URL = '/data-admin/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'dist/static'
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'system.User'


APPEND_SLASH=False


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================================
# DataX Configuration (v1.1.x)
# ============================================================================
# DataX安装目录
DATAX_HOME = os.environ.get('DATAX_HOME', '/opt/datax')

# DataX使用的Python解释器路径
DATAX_PYTHON = os.environ.get('DATAX_PYTHON', 'python3')

# DataX作业配置文件临时目录
DATAX_JOB_DIR = os.environ.get('DATAX_JOB_DIR', '/tmp/datax_jobs')

# DataX默认速度配置
DATAX_DEFAULT_SPEED = {
    'channel': 1,           # 并发通道数
    'byte': 1048576,        # 字节限速（1MB/s）
    'record': 100000,       # 记录限速
}

# DataX默认错误限制
DATAX_ERROR_LIMIT = {
    'record': 0,            # 错误记录数阈值
    'percentage': 0.02,     # 错误率阈值（2%）
}


SPARK_HOME=os.environ.get('SPARK_HOME', '/opt/spark')
SPARK_MASTER=os.environ.get('SPARK_MASTER', 'spark://localhost:7077')
SPARK_SQL_BIN=os.environ.get('SPARK_SQL_BIN', os.path.join(SPARK_HOME, 'bin', 'spark-sql'))
HIVE_HOME=os.environ.get('HIVE_HOME', '/opt/hive')
HIVE_BIN=os.environ.get('HIVE_BIN', os.path.join(HIVE_HOME, 'bin', 'hive'))
