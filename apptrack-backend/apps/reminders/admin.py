from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    """Admin interface for the Reminder model."""
    
    list_display = (
        'id',
        'user',
        'application',
        'reminder_type',
        'reminder_time',
        'is_sent',
        'sent_at',
    )
    
    list_filter = (
        'reminder_type',
        'is_sent',
        'created_at',
        'updated_at',
    )
    
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'application__position',
        'application__company',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'sent_at',
    )
    
    date_hierarchy = 'reminder_time'
    
    fieldsets = (
        (_('Reminder Details'), {
            'fields': (
                'user',
                'application',
                'reminder_type',
                'reminder_time',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_sent',
                'sent_at',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """
        Only superusers can add reminders through the admin.
        Regular users should use the API.
        """
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """
        Only superusers can change reminders through the admin.
        """
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """
        Only superusers can delete reminders through the admin.
        """
        return request.user.is_superuser
