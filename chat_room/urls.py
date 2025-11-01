from django.urls import path
from .views import (
    DoctorListView,
    PatientListView,
    ConversationListView,
    ChatHistoryView,
    UnreadMessagesCountView
)

urlpatterns = [
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('patients/', PatientListView.as_view(), name='patient-list'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('history/<int:user_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('unread-count/', UnreadMessagesCountView.as_view(), name='unread-count'),
]