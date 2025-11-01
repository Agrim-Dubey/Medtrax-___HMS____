from django.db import models
from django.utils import timezone
from Authapi.models import CustomUser


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='chat/attachments/%Y/%m/%d/', null=True, blank=True)
    
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
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


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


class Conversation(models.Model):
    participant1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_as_participant1')
    participant2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_as_participant2')
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_conversation'
        unique_together = ('participant1', 'participant2')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation between {self.participant1.username} and {self.participant2.username}"