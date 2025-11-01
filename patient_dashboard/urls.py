from django.urls import path
from .views import PatientDashboardView, PatientUpcomingAppointmentsView,  PatientRecentAppointmentsView

urlpatterns = [
    path('profile/', PatientDashboardView.as_view(), name='patient-dashboard-profile'),
    path('appointments/', PatientUpcomingAppointmentsView.as_view(), name='patient-upcoming-appointments'),
    path('appointments/recent/', PatientRecentAppointmentsView.as_view(), name='patient-recent-appointments'),
]