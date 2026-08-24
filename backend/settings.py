import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('DJANGO_ENV', 'development') == 'production':
        raise RuntimeError('DJANGO_SECRET_KEY must be set in production.')
    SECRET_KEY = 'django-insecure-development-only-change-me'

DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'rest_framework.authtoken',
    'code_generator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173'
).split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# These remain off locally, but default to safe values when DJANGO_DEBUG=false.
SECURE_SSL_REDIRECT = os.environ.get(
    'DJANGO_SECURE_SSL_REDIRECT', str(not DEBUG)
).lower() in ('1', 'true', 'yes')
SESSION_COOKIE_SECURE = os.environ.get(
    'DJANGO_SESSION_COOKIE_SECURE', str(not DEBUG)
).lower() in ('1', 'true', 'yes')
CSRF_COOKIE_SECURE = os.environ.get(
    'DJANGO_CSRF_COOKIE_SECURE', str(not DEBUG)
).lower() in ('1', 'true', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get(
    'DJANGO_SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0'
))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Flutter Builder API',
    'DESCRIPTION': 'API for generating Flutter applications from JSON specifications.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'displayRequestDuration': True,
    },
}

# Flutter Generation Settings
FLUTTER_SDK_PATH = os.environ.get('FLUTTER_SDK_PATH', '/usr/local/flutter')
ANDROID_SDK_PATH = os.environ.get(
    'ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
JAVA_HOME = os.environ.get('JAVA_HOME')
FLUTTER_VERSION = '3.22.0'
DART_SDK_PATH = os.environ.get('DART_SDK_PATH', '/usr/local/dart-sdk')

# Project Generation Settings
MAX_PROJECTS_PER_USER = 10
PROJECT_RETENTION_DAYS = 30
MAX_ACTIVE_JOBS_PER_USER = int(os.environ.get('MAX_ACTIVE_JOBS_PER_USER', '2'))
MAX_QUEUED_JOBS_PER_USER = int(os.environ.get('MAX_QUEUED_JOBS_PER_USER', '3'))
BACKGROUND_JOB_MAX_WORKERS = int(os.environ.get('BACKGROUND_JOB_MAX_WORKERS', '2'))

# How long (seconds) an unused Flutter preview process is left running
PREVIEW_IDLE_TIMEOUT = 10 * 60
