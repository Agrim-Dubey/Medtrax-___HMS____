from datetime import timedelta
from pathlib import Path
import os
import sys
from corsheaders.defaults import default_headers
from decouple import config
import dj_database_url

# BASE_DIR points to repository root (medtrax-backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

SECRET_KEY = config('SECRET_KEY')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'SAMEORIGIN'

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
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'django_prometheus',
    'authentication',
    'chat_room',
    'videocounselling',
    'appointments',
    'doctor_dashboard',
    'community',
    'patient_dashboard',
    'prescription',
    'ai_agents',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

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

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

db_config = dj_database_url.parse(
    config('DATABASE_URL'),
    conn_max_age=600,
    ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool),
)
if 'postgresql' in db_config.get('ENGINE', ''):
    db_config['ENGINE'] = 'django_prometheus.db.backends.postgresql'
elif 'sqlite3' in db_config.get('ENGINE', ''):
    try:
        import django_prometheus.db.backends.sqlite3
        db_config['ENGINE'] = 'django_prometheus.db.backends.sqlite3'
    except ImportError:
        pass

DATABASES = {
    'default': db_config
}

AUTH_USER_MODEL = 'authentication.CustomUser'
AUTH_PASSWORD_VALIDATORS = []

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=1, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=30, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]

CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SAMESITE = 'None'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

REDIS_URL = config('REDIS_URL')

CACHES = {
    'default': {
        'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'authentication.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '1000/hour',
        'auth_anon': '20/hour',
        'auth_user': '100/hour',
        'otp': '10/hour',
        'login': '10/hour',
        'appointment_booking': '20/hour',
        'appointment_actions': '100/hour',
        'dashboard': '200/hour',
        'chat_message': '100/hour',
        'chat_group': '20/hour',
        'chat_connection': '30/hour',
        'chat_search': '50/hour',
        'chat_read': '300/hour',
    }
}

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@medtrax.me')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AI Clinical Agents (Hybrid Deterministic + Optional LLM)
AI_LLM_PROVIDER = config('AI_LLM_PROVIDER', default='none')
AI_LLM_API_KEY = config('AI_LLM_API_KEY', default='')
AI_LLM_MODEL = config('AI_LLM_MODEL', default='')
AI_LLM_TIMEOUT_SECONDS = config('AI_LLM_TIMEOUT_SECONDS', default=8, cast=int)
AI_LLM_MAX_TOKENS = config('AI_LLM_MAX_TOKENS', default=600, cast=int)
AI_MAX_INPUT_CHARS = config('AI_MAX_INPUT_CHARS', default=2000, cast=int)
