"""
Celery tasks for the applications app.
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail

from .models import Reminder, Application

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_reminder_email(self, reminder_id):
    """
    Send a reminder email for a specific application.
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        
        # Skip if already sent
        if reminder.is_sent:
            logger.info(f"Reminder {reminder_id} already sent, skipping")
            return
            
        application = reminder.application
        user = application.owner
        
        # Prepare email context
        context = {
            'user': user,
            'application': application,
            'reminder': reminder,
            'site_name': settings.SITE_NAME,
            'site_domain': settings.SITE_DOMAIN,
        }
        
        # Render email templates
        subject = f"Reminder: {application.title} at {application.organization}"
        text_message = render_to_string('emails/reminder.txt', context)
        html_message = render_to_string('emails/reminder.html', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Update reminder status
        reminder.is_sent = True
        reminder.sent_at = timezone.now()
        reminder.save()
        
        logger.info(f"Successfully sent reminder {reminder_id} to {user.email}")
        
    except Reminder.DoesNotExist:
        logger.error(f"Reminder {reminder_id} not found")
    except Exception as e:
        logger.error(f"Error sending reminder {reminder_id}: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes


@shared_task
def send_scheduled_reminders():
    """
    Send all reminders that are due.
    """
    now = timezone.now()
    reminders = Reminder.objects.filter(
        remind_at__lte=now,
        is_sent=False
    ).select_related('application', 'application__owner')
    
    logger.info(f"Found {reminders.count()} reminders to send")
    
    for reminder in reminders:
        send_reminder_email.delay(reminder.id)
    
    return f"Processed {reminders.count()} reminders"


@shared_task
def cleanup_old_data():
    """
    Clean up old data to keep the database size in check.
    """
    # Delete soft-deleted applications older than 1 year
    one_year_ago = timezone.now() - timedelta(days=365)
    deleted_count, _ = Application.all_objects.filter(
        is_deleted=True,
        deleted_at__lte=one_year_ago
    ).delete()
    
    # Delete old status history entries for completed applications
    completed_apps = Application.objects.filter(
        status__in=[Application.ApplicationStatus.REJECTED, 
                   Application.ApplicationStatus.WITHDRAWN,
                   Application.ApplicationStatus.OFFER]
    )
    
    # Keep only the most recent status change for each status
    for app in completed_apps:
        # Get the most recent status change for each status
        status_changes = (
            app.status_history.values('to_status')
            .annotate(max_date=models.Max('created_at'))
        )
        
        # Get the IDs of the most recent status changes to keep
        keep_ids = []
        for change in status_changes:
            latest = (
                app.status_history
                .filter(to_status=change['to_status'])
                .order_by('-created_at')
                .values_list('id', flat=True)
                .first()
            )
            if latest:
                keep_ids.append(latest)
        
        # Delete all other status changes
        deleted_status = (
            app.status_history
            .exclude(id__in=keep_ids)
            .delete()
        )
        deleted_count += deleted_status[0]
    
    return f"Cleaned up {deleted_count} old records"
