from decouple import config
from .base import *

DEBUG = True

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='*',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default="http://localhost:5173,http://localhost:5174",
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
