from django.urls import path
from .views import PatientDashboardView, PatientUpcomingAppointmentsView

urlpatterns = [
    path('profile/', PatientDashboardView.as_view(), name='patient-dashboard-profile'),
    path('appointments/', PatientUpcomingAppointmentsView.as_view(), name='patient-upcoming-appointments'),
]