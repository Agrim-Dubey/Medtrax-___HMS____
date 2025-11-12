from datetime import timedelta
from pathlib import Path
import os
from decouple import config
from dotenv import load_dotenv
import dj_database_url

# ============================================================
# BASE CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Detect environment
if os.path.exists("/.dockerenv"):
    load_dotenv(os.path.join(BASE_DIR, ".env.docker"))
    print("Running inside Docker → Loaded .env.docker")
else:
    load_dotenv(os.path.join(BASE_DIR, ".env.local"))
    print("Running locally → Loaded .env.local")

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "13.49.67.184",
    "medtrax.me",
    "www.medtrax.me",
    "med-trax.me",
    "www.med-trax.me",
]

# ============================================================
# SECURITY
# ============================================================

SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    'jazzmin',
    'daphne',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',

    # Local apps
    'Authapi',
    'chat_room',
    'videocounselling',
    'appointments',
    'doctor_dashboard',
    'community',
    'patient_dashboard',
]

# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be at the top
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================
# URLS & WSGI/ASGI
# ============================================================

ROOT_URLCONF = 'medtrax.urls'
WSGI_APPLICATION = 'medtrax.wsgi.application'
ASGI_APPLICATION = 'medtrax.asgi.application'

# ============================================================
# DATABASE
# ============================================================

database_url = config('DATABASE_URL', default=None)
if database_url and not database_url.startswith('sqlite'):
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    DATABASES = {'default': dj_database_url.parse(database_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================================
# AUTH
# ============================================================

AUTH_USER_MODEL = 'Authapi.CustomUser'
AUTH_PASSWORD_VALIDATORS = []
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
ARGON2_PARAMETERS = {'time_cost': 2, 'memory_cost': 512, 'parallelism': 2}

# ============================================================
# REST FRAMEWORK & JWT
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'Authapi.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('PAGE_SIZE', default=50, cast=int),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=1, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=30, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
}

# ============================================================
# CORS & CSRF CONFIGURATION
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "https://medtrax.me",
    "https://www.medtrax.me",
    "https://med-trax.me",
    "https://www.med-trax.me",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://medtrax.me",
    "https://www.medtrax.me",
    "https://med-trax.me",
    "https://www.med-trax.me",
]
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = None
CSRF_USE_SESSIONS = False

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_DOMAIN = None

# ============================================================
# STATIC & MEDIA
# ============================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ============================================================
# CELERY
# ============================================================

REDIS_HOST = config('REDIS_HOST', default='redis')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default=None)

CELERY_BROKER_URL = f'redis://{":" + REDIS_PASSWORD + "@" if REDIS_PASSWORD else ""}{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = config('TIME_ZONE', default='UTC')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ============================================================
# CHANNELS (WEBSOCKETS)
# ============================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (
                    REDIS_HOST if REDIS_PASSWORD is None else f":{REDIS_PASSWORD}@{REDIS_HOST}",
                    REDIS_PORT
                )
            ],
        },
    },
}

# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# ============================================================
# GENERAL
# ============================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
