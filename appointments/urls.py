from django.urls import path
from .views import (
    PatientBookAppointmentView,
    PatientAppointmentListView,
    
    DoctorAppointmentRequestsView,
    DoctorAppointmentsListView,
    DoctorAcceptAppointmentView,
    DoctorRejectAppointmentView,
    AvailableDoctorsListView
)

urlpatterns = [
    # Patient endpoints
    path('patient/book/', PatientBookAppointmentView.as_view(), name='patient-book-appointment'),
    path('patient/list/', PatientAppointmentListView.as_view(), name='patient-appointments-list'),
    path('doctors/available/', AvailableDoctorsListView.as_view(), name='available-doctors'),
    
    # Doctor endpoints
    path('doctor/requests/', DoctorAppointmentRequestsView.as_view(), name='doctor-appointment-requests'),
    path('doctor/appointments/', DoctorAppointmentsListView.as_view(), name='doctor-appointments-list'),
    path('doctor/<int:appointment_id>/accept/', DoctorAcceptAppointmentView.as_view(), name='doctor-accept-appointment'),
    path('doctor/<int:appointment_id>/reject/', DoctorRejectAppointmentView.as_view(), name='doctor-reject-appointment'),
]