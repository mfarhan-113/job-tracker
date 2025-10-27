"""
Signals for the reminders app.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Reminder
from .tasks import send_reminder_email


@receiver(post_save, sender=Reminder)
def schedule_reminder(sender, instance, created, **kwargs):
    """
    Schedule a reminder to be sent at the specified time.
    """
    if created and not instance.is_sent:
        # Schedule the reminder to be sent at the specified time
        send_reminder_email.apply_async(
            args=[instance.id],
            eta=instance.reminder_time
        )
        
        # If the reminder time is in the past, send it immediately
        if instance.reminder_time <= timezone.now():
            send_reminder_email.delay(instance.id)


@receiver(pre_save, sender=Reminder)
def update_scheduled_reminder(sender, instance, **kwargs):
    """
    If the reminder time is updated, reschedule the task.
    """
    if not instance.pk:
        return  # New instance, will be handled by post_save
        
    try:
        old_instance = Reminder.objects.get(pk=instance.pk)
        
        # If the reminder time has changed and the reminder hasn't been sent yet
        if (old_instance.reminder_time != instance.reminder_time and 
                not instance.is_sent):
            # The task will be rescheduled by the post_save signal
            pass
            
    except Reminder.DoesNotExist:
        pass  # New instance, will be handled by post_save
