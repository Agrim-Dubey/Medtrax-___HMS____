# medtrax/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Medtrax Healthcare API",
        default_version='v1',
        description="""
        ## Medtrax Healthcare API Documentation

        **Base URL:** `/api/`

        Example: `/api/appointments/patient/book/`

        ### Authentication
        - Use JWT tokens in the Authorization header:
          ```
          Authorization: Bearer <token>
          ```
        """,
        terms_of_service="https://medtrax.me/terms/",
        contact=openapi.Contact(email="support@medtrax.me", name="Medtrax Support", url="https://medtrax.me/support"),
        license=openapi.License(name="Proprietary License", url="https://medtrax.me/license"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('Authapi.urls')),
    path('api/chat/', include('chat_room.urls')),
    path('api/doctor/dashboard/', include('doctor_dashboard.urls')),
    path('api/patient/dashboard/', include('patient_dashboard.urls')),
    path('api/community/', include('community.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
