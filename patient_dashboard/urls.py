from django.urls import path
from .views import PatientDashboardView

urlpatterns = [
    path('profile/', PatientDashboardView.as_view(), name='patient-dashboard-profile'),
]