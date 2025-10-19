from django.urls import path
from . import views



urlpatterns = [
    path('api/signup/', views.SignupView.as_view(), name='signup'),
    path('api/verify-signup-otp/', views.VerifySignupOTPView.as_view(), name='verify_signup_otp'),
    path('api/resend-signup-otp/', views.ResendSignupOTPView.as_view(), name='resend_signup_otp'),
    path('api/complete-doctor-profile/', views.DoctorDetailsView.as_view(), name='complete_doctor_profile'),
    path('api/complete-patient-profile/', views.PatientDetailsView.as_view(), name='complete_patient_profile'),
    path('api/doctor-login/', views.DoctorLoginView.as_view(), name='doctor_login'),
    path('api/patient-login/', views.PatientLoginView.as_view(), name='patient_login'),
    path('api/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('api/verify-password-reset-otp/', views.VerifyPasswordResetOTPView.as_view(), name='verify_password_reset_otp'),
    path('api/reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('api/resend-password-reset-otp/', views.ResendPasswordResetOTPView.as_view(), name='resend_password_reset_otp'),
    path('api/check-account-status/', views.CheckAccountStatusView.as_view(), name='check_account_status'),
]