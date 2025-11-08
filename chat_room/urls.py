from django.urls import path
from .views import (
    PatientChatViewSet,
    DoctorChatViewSet,
    ChatRoomViewSet,
    test_chat_doctor,
    test_chat_patient,
)

urlpatterns = [
    path('patient/doctors/', PatientChatViewSet.as_view({'get': 'list_doctor_chats'}), name='patient-doctor-chats'),
    path('patient/groups/', PatientChatViewSet.as_view({'get': 'list_groups'}), name='patient-groups'),
    path('patient/groups/join/', PatientChatViewSet.as_view({'post': 'join_group'}), name='patient-join-group'),
    
    path('doctor/patients/', DoctorChatViewSet.as_view({'get': 'list_patient_chats'}), name='doctor-patient-chats'),
    path('doctor/doctors/', DoctorChatViewSet.as_view({'get': 'list_doctor_chats'}), name='doctor-doctor-chats'),
    path('doctor/connection-request/', DoctorChatViewSet.as_view({'post': 'send_connection_request'}), name='doctor-send-request'),
    path('doctor/connection-requests/pending/', DoctorChatViewSet.as_view({'get': 'list_pending_requests'}), name='doctor-pending-requests'),
    path('doctor/connection-requests/<int:pk>/accept/', DoctorChatViewSet.as_view({'post': 'accept_connection'}), name='doctor-accept-request'),
    path('doctor/connection-requests/<int:pk>/reject/', DoctorChatViewSet.as_view({'post': 'reject_connection'}), name='doctor-reject-request'),
    path('doctor/search/', DoctorChatViewSet.as_view({'get': 'search_doctors'}), name='doctor-search'),
    
    path('rooms/<int:pk>/', ChatRoomViewSet.as_view({'get': 'retrieve'}), name='chat-room-detail'),
    path('rooms/<int:pk>/messages/', ChatRoomViewSet.as_view({'post': 'send_message'}), name='chat-send-message'),
    path('rooms/<int:pk>/read/', ChatRoomViewSet.as_view({'post': 'mark_as_read'}), name='chat-mark-read'),
    path('test/doctor/<int:room_id>/', test_chat_doctor, name='test-chat-doctor'),
    path('test/patient/<int:room_id>/', test_chat_patient, name='test-chat-patient'),

]