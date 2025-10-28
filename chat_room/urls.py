from django.urls import path
from .views import UserListView, ChatHistoryView, UnreadCountView, MarkAsReadView

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    path('history/<int:user_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),
    path('mark-as-read/', MarkAsReadView.as_view(), name='mark-as-read'),
]