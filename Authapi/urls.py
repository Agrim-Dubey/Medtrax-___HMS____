from django.urls import path
from . import views

urlpatterns = [
    path('api/register/', views.register_view, name='register'),
    path('api/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('api/login/', views.login_view, name='login'),
    path('api/forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('api/reset-password/', views.reset_password_view, name='reset_password'),
]