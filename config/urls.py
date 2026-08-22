from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from rest_framework.throttling import BaseThrottle
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg import openapi
from config.health import healthz


class NoThrottle(BaseThrottle):
    def allow_request(self, request, view):
        return True
    def wait(self):
        return None


class DynamicSchemaGenerator(OpenAPISchemaGenerator):
    def get_endpoints(self, request):
        return super().get_endpoints(request)


schema_view = get_schema_view(
    openapi.Info(
        title="Medtrax Healthcare API",
        default_version='v1',
        description="""
        ## Medtrax Healthcare API Documentation

        **Base URL:** `/api/`

        Example: `/api/appointments/patient/book/`

        ### Authentication
        Use JWT Bearer tokens:
        ```
        Authorization: Bearer <your_token>
        ```
        """,
        contact=openapi.Contact(email="support@medtrax.me"),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
    generator_class=DynamicSchemaGenerator,
)


def patch_throttle(view_func):
    view_func.cls.throttle_classes = [NoThrottle]
    return view_func


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('Authapi.urls')),
    path('api/chat/', include('chat_room.urls')),
    path('api/doctor/dashboard/', include('doctor_dashboard.urls')),
    path('api/patient/dashboard/', include('patient_dashboard.urls')),
    path('api/community/', include('community.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('vapi/video/', include('videocounselling.urls')),
    path('api/prescriptions/', include('prescription.urls')),
    path('healthz/', healthz, name='healthz'),
    path('', include('django_prometheus.urls')),

    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        patch_throttle(schema_view.without_ui(cache_timeout=0)),
        name='schema-json'
    ),
    path('swagger/', patch_throttle(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    path('redoc/', patch_throttle(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),
]