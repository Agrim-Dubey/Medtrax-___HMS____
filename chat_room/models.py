from django.db import models
from Authapi.models import CustomUser


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'chat_message'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}"


class UserOnlineStatus(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='online_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_user_online_status'
        indexes = [
            models.Index(fields=['user', 'is_online']),
        ]

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"