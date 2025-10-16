from django.urls import path
from . import views

urlpatterns = [
    path('api/docregister/',views.DoctorRegisterView.as_view(), name='doctor_register'),
    path('api/doclogin/',views.DoctorLoginView.as_view(), name='doctor_login'),
    path('api/patientregister/',views.PatientRegisterView.as_view(),name ='patient_register'),
    path('api/patientlogin/',views.PatientLoginView.as_view(),name='patient_login'),
    path('api/Doctor-Details/',views. DoctorDetailsView.as_view(),name='doctor_details_page'),
    path('api/Patient-Details/',views.PatientDetailsView.as_view(),name='patient_details_page'),
    path('api/forgot-password/',views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('api/verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('api/verify-password-reset-otp/',views.VerifyPasswordResetOTPView.as_view(), name='verify_reset_password_otp'),
    path('api/reset-password/',views.ResetPasswordView.as_view(), name='reset_password'),
    path('api/resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'), 
]