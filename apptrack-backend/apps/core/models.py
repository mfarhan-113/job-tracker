"""
Core models and utilities for the apptrack project.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='updated at')

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    An abstract base class model that provides soft delete functionality.
    """
    is_deleted = models.BooleanField(default=False, verbose_name='is deleted')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='deleted at')

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Override delete to perform a soft delete."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Perform a hard delete."""
        return super().delete(using=using, keep_parents=keep_parents)
