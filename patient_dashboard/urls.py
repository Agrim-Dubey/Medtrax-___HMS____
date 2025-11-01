from django.urls import path
from .views import PatientDashboardView,PatientUpcomingAppointmentsView, PatientRecentAppointmentsView,PatientDashboardStatsView

urlpatterns = [
    path('profile/', PatientDashboardView.as_view(), name='patient-dashboard-profile'),
    path('appointments/', PatientUpcomingAppointmentsView.as_view(), name='patient-upcoming-appointments'),
    path('appointments/recent/', PatientRecentAppointmentsView.as_view(), name='patient-recent-appointments'),
    path('stats/', PatientDashboardStatsView.as_view(), name='patient-dashboard-stats'),
]