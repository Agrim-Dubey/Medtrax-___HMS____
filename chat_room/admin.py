from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Message, UserOnlineStatus, Conversation


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'sender_name',
        'receiver_name',
        'short_content',
        'is_read_badge',
        'timestamp'
    ]
    
    list_filter = [
        'is_read',
        'timestamp',
        'sender__role',
        'receiver__role'
    ]
    
    search_fields = [
        'sender__username',
        'sender__email',
        'receiver__username',
        'receiver__email',
        'content'
    ]
    
    readonly_fields = ['timestamp', 'read_at']
    
    fieldsets = (
        ('Message Details', {
            'fields': (
                'sender',
                'receiver',
                'content',
                'attachment'
            )
        }),
        ('Status', {
            'fields': (
                'is_read',
                'read_at'
            )
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )
    
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def sender_name(self, obj):
        url = reverse('admin:Authapi_customuser_change', args=[obj.sender.id])
        return format_html('<a href="{}">{}</a>', url, obj.sender.username)
    sender_name.short_description = 'From'
    
    def receiver_name(self, obj):
        url = reverse('admin:Authapi_customuser_change', args=[obj.receiver.id])
        return format_html('<a href="{}">{}</a>', url, obj.receiver.username)
    receiver_name.short_description = 'To'
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Message'
    
    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange;">○ Unread</span>')
    is_read_badge.short_description = 'Status'
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = "Mark as Read"


@admin.register(UserOnlineStatus)
class UserOnlineStatusAdmin(admin.ModelAdmin):
    """Admin panel for User Online Status"""
    
    list_display = [
        'user_name',
        'is_online_badge',
        'last_seen'
    ]
    
    list_filter = ['is_online', 'last_seen']
    
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = ['last_seen']
    
    def user_name(self, obj):
        url = reverse('admin:Authapi_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_name.short_description = 'User'
    
    def is_online_badge(self, obj):
        if obj.is_online:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Online</span>'
            )
        return format_html(
            '<span style="color: gray;">○ Offline</span>'
        )
    is_online_badge.short_description = 'Status'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin panel for Conversations"""
    
    list_display = [
        'id',
        'participant1_name',
        'participant2_name',
        'last_message_preview',
        'updated_at'
    ]
    
    search_fields = [
        'participant1__username',
        'participant2__username',
        'participant1__email',
        'participant2__email'
    ]
    
    readonly_fields = ['updated_at']
    
    date_hierarchy = 'updated_at'
    ordering = ['-updated_at']
    
    def participant1_name(self, obj):
        url = reverse('admin:Authapi_customuser_change', args=[obj.participant1.id])
        return format_html('<a href="{}">{}</a>', url, obj.participant1.username)
    participant1_name.short_description = 'Participant 1'
    
    def participant2_name(self, obj):
        url = reverse('admin:Authapi_customuser_change', args=[obj.participant2.id])
        return format_html('<a href="{}">{}</a>', url, obj.participant2.username)
    participant2_name.short_description = 'Participant 2'
    
    def last_message_preview(self, obj):
        if obj.last_message:
            content = obj.last_message.content
            return content[:40] + '...' if len(content) > 40 else content
        return '-'
    last_message_preview.short_description = 'Last Message'