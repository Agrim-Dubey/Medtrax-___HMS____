from django.urls import path
from . import views

urlpatterns = [
    path("test/doctor/<int:room_id>/", views.test_video_doctor, name="video-test-doctor"),
    path("test/patient/<int:room_id>/", views.test_video_patient, name="video-test-patient"),
]
