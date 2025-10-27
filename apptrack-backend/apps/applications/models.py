"""
Models for the applications app.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

from apps.core.models import TimeStampedModel


class Application(TimeStampedModel):
    """
    Model to track job/scholarship applications.
    """
    class ApplicationKind(models.TextChoices):
        JOB = 'job', _('Job')
        SCHOLARSHIP = 'scholarship', _('Scholarship')

    class ApplicationStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        APPLIED = 'applied', _('Applied')
        INTERVIEW = 'interview', _('Interview')
        OFFER = 'offer', _('Offer Received')
        REJECTED = 'rejected', _('Rejected')
        WITHDRAWN = 'withdrawn', _('Withdrawn')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('owner')
    )
    kind = models.CharField(
        max_length=20,
        choices=ApplicationKind.choices,
        verbose_name=_('kind')
    )
    title = models.CharField(max_length=255, verbose_name=_('title'))
    organization = models.CharField(max_length=255, verbose_name=_('organization'))
    location = models.CharField(max_length=255, blank=True, verbose_name=_('location'))
    country = models.CharField(max_length=100, blank=True, verbose_name=_('country'))
    source_url = models.URLField(blank=True, verbose_name=_('source URL'))
    applied_date = models.DateField(null=True, blank=True, verbose_name=_('applied date'))
    deadline = models.DateField(null=True, blank=True, verbose_name=_('deadline'))
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        verbose_name=_('status')
    )
    priority = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name=_('priority')
    )
    notes = models.TextField(blank=True, verbose_name=_('notes'))
    tags = models.JSONField(default=list, blank=True, verbose_name=_('tags'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('application')
        verbose_name_plural = _('applications')
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['owner', 'deadline']),
            models.Index(fields=['owner', 'kind']),
        ]

    def __str__(self):
        return f"{self.title} at {self.organization}"


class Attachment(TimeStampedModel):
    """
    Model to store files attached to applications.
    """
    class DocumentType(models.TextChoices):
        CV = 'cv', _('CV/Resume')
        COVER_LETTER = 'cover_letter', _('Cover Letter')
        TRANSCRIPT = 'transcript', _('Transcript')
        CERTIFICATE = 'certificate', _('Certificate')
        OTHER = 'other', _('Other')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('application')
    )
    file = models.FileField(upload_to='attachments/%Y/%m/%d/', verbose_name=_('file'))
    name = models.CharField(max_length=255, verbose_name=_('name'))
    file_type = models.CharField(max_length=100, verbose_name=_('file type'))
    file_size = models.BigIntegerField(help_text=_('File size in bytes'), verbose_name=_('file size'))
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        verbose_name=_('document type')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        verbose_name=_('uploaded by')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')

    def __str__(self):
        return self.name


class StatusHistory(TimeStampedModel):
    """
    Model to track status changes of applications.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('application')
    )
    from_status = models.CharField(max_length=20, verbose_name=_('from status'))
    to_status = models.CharField(max_length=20, verbose_name=_('to status'))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_changes',
        verbose_name=_('changed by')
    )
    notes = models.TextField(blank=True, verbose_name=_('notes'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('status history')
        verbose_name_plural = _('status histories')

    def __str__(self):
        return f"{self.application}: {self.from_status} → {self.to_status}"
