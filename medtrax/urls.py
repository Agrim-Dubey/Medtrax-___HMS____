from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Medtrax Healthcare API",
        default_version='v1',
        description="""
        # Healthcare Management System - Medtrax API Documentation

        ## Authentication Flow
        
        ### For New Users:
        1. **Signup** → Receive OTP via email
        2. **Verify OTP** → Email verified
        3. **Complete Profile** → Doctor or Patient details
        4. **Login** → Receive JWT tokens
        
        ### For Existing Users:
        1. **Login** → Use credentials to get JWT tokens
        2. **Use Bearer Token** → Add to Authorization header
        
        ### For Password Reset:
        1. **Forgot Password** → Receive OTP via email
        2. **Verify Reset OTP** → OTP validated
        3. **Reset Password** → Set new password
        4. **Login** → Use new credentials
        
        ## Authorization
        Most endpoints require JWT authentication. Add the token to requests:
        ```
        Authorization: Bearer <your_token_here>
        ```
        """,
        terms_of_service="https://medtrax.me/terms/",
        contact=openapi.Contact(
            name="Medtrax API Support",
            email="support@medtrax.me",
            url="https://medtrax.me/support"
        ),
        license=openapi.License(
            name="Proprietary License",
            url="https://medtrax.me/license"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('Authapi.urls')),
    path('api/chat/', include('chat_room.urls')),
    path('api/doctor/dashboard/', include('doctor_dashboard.urls')),
    path('api/patient/dashboard/', include('patient_dashboard.urls')),
    path('api/community/', include('community.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]