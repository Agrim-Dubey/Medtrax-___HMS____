from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.get_dashboard_stats, name='dashboarddoctorstats'),
    path('appointments/upcoming/', views.get_upcoming_appointments, name='upcomingappointments'),
    path('reviews/recent/', views.get_recent_reviews, name='recentreviews'),
    path('stats/weekly-patients/', views.get_weekly_patient_stats, name='weeklypatientstats'),
]