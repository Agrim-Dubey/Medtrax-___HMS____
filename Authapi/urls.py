from django.urls import path
from . import views

urlpatterns = [
    path('api/docregister/',views.doctor_register_view, name='doctor_register'),
    path('api/doclogin/',views.patient_login_view, name='doctor_login'),
    path('api/patientregister/',views.patient_register_view,name ='patient_register'),
    path('api/patientlogin/',views.patient_login_view,name='patient_login'),
    path('api/forgot-password/',views.forgot_password_view, name='forgot_password'),
    path('api/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('api/reset-password/',views.reset_password_view, name='reset_password'),
    path('api/resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('api/Doctor-Details/',views.doctor_details_view,name='doctor_details_page'),
    path('api/Patient-Details/',views.patients_details_view,name='patient_details_page'),
]