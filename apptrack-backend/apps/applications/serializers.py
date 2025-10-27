""" 
Serializers for the applications app.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.applications.models import Application, Attachment, StatusHistory
from apps.reminders.models import Reminder
from apps.core.serializers import DynamicFieldsModelSerializer


class StatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for status history entries."""
    changed_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for file attachments."""
    url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'name', 'file_type', 'file_size',
            'document_type', 'uploaded_by', 'created_at', 'url'
        ]
        read_only_fields = ['id', 'created_at', 'uploaded_by']

    def get_url(self, obj):
        """
        Get the download URL for the file.
        In a real implementation, this would generate a pre-signed URL
        """
        if obj.file:
            return obj.file.url
        return None

    def get_file_name(self, obj):
        """Get the original filename."""
        return obj.file.name.split('/')[-1] if obj.file else None

    def get_file_size(self, obj):
        """Get the file size in a human-readable format."""
        if not obj.file:
            return None
        size = obj.file.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0 or unit == 'GB':
                break
            size /= 1024.0
        return f"{size:.1f} {unit}"

    def get_file_type(self, obj):
        """Get the file type."""
        if not obj.file:
            return None
        return obj.file.name.split('.')[-1].upper()


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for application reminders."""
    class Meta:
        model = Reminder
        fields = ['id', 'remind_at', 'channel', 'message', 'is_sent', 'created_at']
        read_only_fields = ['id', 'is_sent', 'created_at']


class ApplicationSerializer(DynamicFieldsModelSerializer):
    """Serializer for job/scholarship applications."""
    attachments = AttachmentSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)
    reminders = ReminderSerializer(many=True, read_only=True)
    owner = serializers.StringRelatedField(read_only=True)
    current_status = serializers.CharField(source='get_status_display', read_only=True)
    application_kind = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'kind', 'application_kind', 'title', 'organization', 'location', 'country',
            'source_url', 'applied_date', 'deadline', 'status', 'current_status', 'priority',
            'notes', 'tags', 'owner', 'created_at', 'updated_at', 'attachments',
            'status_history', 'reminders'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def validate(self, data):
        """
        Validate application data.
        - Ensure deadline is in the future when creating a new application
        - Ensure applied_date is not in the future
        """
        if self.instance is None and 'deadline' in data and data['deadline']:
            from django.utils import timezone
            if data['deadline'] < timezone.now().date():
                raise serializers.ValidationError({
                    'deadline': _('Deadline cannot be in the past')
                })

        if 'applied_date' in data and data['applied_date']:
            from django.utils import timezone
            if data['applied_date'] > timezone.now().date():
                raise serializers.ValidationError({
                    'applied_date': _('Application date cannot be in the future')
                })

        return data


class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for application lists."""
    current_status = serializers.CharField(source='get_status_display')
    application_kind = serializers.CharField(source='get_kind_display')
    attachment_count = serializers.IntegerField(source='attachments.count', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'kind', 'application_kind', 'title', 'organization',
            'status', 'current_status', 'deadline', 'applied_date',
            'created_at', 'attachment_count'
        ]
        read_only_fields = fields


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating application status."""
    note = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Application
        fields = ['status', 'note']

    def update(self, instance, validated_data):
        note = validated_data.pop('note', '')
        from_status = instance.status
        to_status = validated_data.get('status', from_status)
        
        # Only create status history if status changed
        if from_status != to_status:
            StatusHistory.objects.create(
                application=instance,
                from_status=from_status,
                to_status=to_status,
                changed_by=self.context['request'].user,
                notes=note
            )
        
        return super().update(instance, validated_data)
