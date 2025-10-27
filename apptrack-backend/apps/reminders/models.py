from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.applications.models import Application


class Reminder(models.Model):
    """Model for storing application deadline reminders."""
    
    class ReminderType(models.TextChoices):
        EMAIL = 'email', _('Email')
        NOTIFICATION = 'notification', _('Notification')
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('application')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('user')
    )
    
    reminder_type = models.CharField(
        _('reminder type'),
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.EMAIL
    )
    
    reminder_time = models.DateTimeField(
        _('reminder time'),
        help_text=_('When the reminder should be sent')
    )
    
    is_sent = models.BooleanField(
        _('is sent'),
        default=False,
        help_text=_('Whether the reminder has been sent')
    )
    
    sent_at = models.DateTimeField(
        _('sent at'),
        null=True,
        blank=True,
        help_text=_('When the reminder was actually sent')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('reminder')
        verbose_name_plural = _('reminders')
        ordering = ['reminder_time']
        indexes = [
            models.Index(fields=['is_sent', 'reminder_time']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.application.position} at {self.reminder_time}"
    
    def mark_as_sent(self):
        """Mark the reminder as sent."""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['is_sent', 'sent_at', 'updated_at'])
    
    def is_due(self):
        """Check if the reminder is due to be sent."""
        return not self.is_sent and self.reminder_time <= timezone.now()
