"""
Celery tasks for the reminders app.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models import Reminder

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_reminder_email(self, reminder_id):
    """
    Send a reminder email for a single reminder.
    
    Args:
        reminder_id: The ID of the reminder to send
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id, is_sent=False)
        
        # Check if the reminder is still relevant
        if reminder.reminder_time > timezone.now():
            logger.info(
                "Reminder %s is not due yet, rescheduling...",
                reminder_id
            )
            # Reschedule the task for the reminder time
            send_reminder_email.apply_async(
                args=[reminder_id],
                eta=reminder.reminder_time
            )
            return
        
        # Prepare email context
        context = {
            'user': reminder.user,
            'application': reminder.application,
            'reminder': reminder,
            'site_name': settings.SITE_NAME,
            'domain': settings.FRONTEND_URL,
        }
        
        # Render email content
        subject = _("Reminder: %(position)s at %(company)s") % {
            'position': reminder.application.position,
            'company': reminder.application.company or _('a company')
        }
        
        message = render_to_string(
            'emails/reminder.txt',
            context
        )
        
        html_message = render_to_string(
            'emails/reminder.html',
            context
        )
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reminder.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark the reminder as sent
        reminder.mark_as_sent()
        logger.info("Successfully sent reminder %s", reminder_id)
        
    except Reminder.DoesNotExist:
        logger.warning("Reminder %s not found or already sent", reminder_id)
    except Exception as exc:
        logger.error(
            "Error sending reminder %s: %s",
            reminder_id,
            str(exc),
            exc_info=True
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry after 5 minutes


@shared_task
def send_due_reminders():
    """
    Task to send all due reminders.
    This should be run periodically (e.g., every 5 minutes) by Celery Beat.
    """
    now = timezone.now()
    due_reminders = Reminder.objects.filter(
        is_sent=False,
        reminder_time__lte=now,
    ).select_related('user', 'application')
    
    count = 0
    for reminder in due_reminders.iterator(chunk_size=100):
        try:
            # Send each reminder as a separate task
            send_reminder_email.delay(reminder.id)
            count += 1
        except Exception as e:
            logger.error(
                "Error queueing reminder %s: %s",
                reminder.id,
                str(e),
                exc_info=True
            )
    
    logger.info("Queued %d due reminders for sending", count)
    return f"Queued {count} reminders for sending"


@shared_task
def cleanup_old_reminders(days=30):
    """
    Clean up old sent reminders.
    
    Args:
        days: Number of days of reminders to keep
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    result = Reminder.objects.filter(
        is_sent=True,
        sent_at__lt=cutoff_date
    ).delete()
    
    logger.info("Cleaned up %d old reminders", result[0])
    return f"Cleaned up {result[0]} old reminders"
