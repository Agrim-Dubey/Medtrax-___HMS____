
from django.contrib import admin
from django.urls import path,include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Medtrax API",
      default_version='v1',
      description="API documentation for Medtrax",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="hehe@hahaha.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

schema_view = get_schema_view(
    openapi.Info(
        title="Healthcare Authentication API",
        default_version='v1',
        description="""
        # Healthcare Management System - Authentication API for Medtrax

        ## Authentication Flow
        
        ### For New Users:
        1. **Signup** → Receive OTP via email
        2. **Verify OTP** → Email verified
        3. **Complete Profile** → Doctor or Patient details
        4. **Login** → Receive JWT tokens
        
        ### For Password Reset:
        1. **Forgot Password** → Receive OTP via email
        2. **Verify Reset OTP** → OTP validated
        3. **Reset Password** → Set new password
        4. **Login** → Use new credentials
        """,
        terms_of_service="https://www.healthcare.com/terms/",
        contact=openapi.Contact(
            name="API Support",
            email="support@healthcare.com",
            url="https://www.healthcare.com/support"
        ),
        license=openapi.License(
            name="Proprietary License",
            url="https://medtrax.me/"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('Authapi.urls')),
    path('swagger/',schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/chat/',include('chat_room.urls')),
]

