from django.urls import path
from .views import (
    DoctorListView,
    PatientListView,
    ConversationListView,
    ChatHistoryView,
    UnreadMessagesCountView,
    UnreadMessagesPerConversationView, 
    DeleteMessageView,  
    SearchMessagesView,  
)

urlpatterns = [
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('patients/', PatientListView.as_view(), name='patient-list'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('history/<int:user_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('unread-count/', UnreadMessagesCountView.as_view(), name='unread-count'),
    path('unread-by-conversation/', UnreadMessagesPerConversationView.as_view(), name='unread-by-conversation'),
    path('messages/<int:message_id>/delete/', DeleteMessageView.as_view(), name='delete-message'),
    path('search/', SearchMessagesView.as_view(), name='search-messages'),
]