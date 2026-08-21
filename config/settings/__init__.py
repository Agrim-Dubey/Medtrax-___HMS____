"""
Settings package initialization for MedTrax backend.

Dynamically loads the appropriate settings module based on DJANGO_ENV:
- 'production' / 'prod': config.settings.production
- 'development' / 'dev' / default: config.settings.development
"""
from decouple import config

DJANGO_ENV = config('DJANGO_ENV', default=None)

if DJANGO_ENV:
    if DJANGO_ENV.lower() in ('prod', 'production'):
        from .production import *
    else:
        from .development import *
else:
    if config('DEBUG', default=False, cast=bool):
        from .development import *
    else:
        from .production import *
