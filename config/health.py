from django.http import JsonResponse
from django.db import connection
from django.core.cache import caches
import time


def healthz(request):
    """
    Lightweight health check endpoint for Docker, Kubernetes, and load balancers.
    Checks connectivity to PostgreSQL database and Redis cache.
    Returns HTTP 200 when healthy, HTTP 503 if any core dependency fails.
    """
    checks = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "services": {
            "database": "unknown",
            "redis": "unknown"
        }
    }
    status_code = 200

    # 1. Verify PostgreSQL connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row and row[0] == 1:
                checks["services"]["database"] = "healthy"
            else:
                checks["services"]["database"] = "unhealthy"
                status_code = 503
    except Exception as e:
        checks["services"]["database"] = f"unhealthy: {str(e)}"
        status_code = 503

    # 2. Verify Redis connectivity
    try:
        cache = caches['default']
        cache.set('__healthcheck__', 'ok', timeout=10)
        val = cache.get('__healthcheck__')
        if val == 'ok':
            checks["services"]["redis"] = "healthy"
        else:
            checks["services"]["redis"] = "unhealthy"
            status_code = 503
    except Exception as e:
        checks["services"]["redis"] = f"unhealthy: {str(e)}"
        status_code = 503

    if status_code != 200:
        checks["status"] = "unhealthy"

    return JsonResponse(checks, status=status_code)
