from django.urls import path
from . import views



urlpatterns = [
    path('/select-role/', views.SelectRoleView.as_view(), name='select_role'),
    path('/clear-role/', views.ClearRoleView.as_view(), name='clear_role'),
    path('/signup/', views.SignupView.as_view(), name='signup'),
    path('/verify-signup-otp/', views.VerifySignupOTPView.as_view(), name='verify_signup_otp'),
    path('/resend-signup-otp/', views.ResendSignupOTPView.as_view(), name='resend_signup_otp'),
    path('/complete-doctor-profile/', views.DoctorDetailsView.as_view(), name='complete_doctor_profile'),
    path('/complete-patient-profile/', views.PatientDetailsView.as_view(), name='complete_patient_profile'),
    path('/doctor-login/', views.DoctorLoginView.as_view(), name='doctor_login'),
    path('/patient-login/', views.PatientLoginView.as_view(), name='patient_login'),
    path('/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('/verify-password-reset-otp/', views.VerifyPasswordResetOTPView.as_view(), name='verify_password_reset_otp'),
    path('/reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('/resend-password-reset-otp/', views.ResendPasswordResetOTPView.as_view(), name='resend_password_reset_otp'),
    path('/check-account-status/', views.CheckAccountStatusView.as_view(), name='check_account_status'),
]