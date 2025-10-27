from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.reminders.models import Reminder
from apps.applications.serializers import ApplicationSerializer


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for the Reminder model."""
    application_details = ApplicationSerializer(
        source='application', 
        read_only=True,
        fields=('id', 'position', 'company', 'status', 'deadline')
    )
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'application', 'application_details', 'reminder_type', 
            'reminder_time', 'is_sent', 'sent_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_sent', 'sent_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'user': {'write_only': True},
            'application': {'required': True}
        }
    
    def validate_reminder_time(self, value):
        """Ensure the reminder time is in the future."""
        from django.utils import timezone
        
        if value <= timezone.now():
            raise serializers.ValidationError(
                _("Reminder time must be in the future.")
            )
        return value
    
    def validate(self, attrs):
        """Validate the reminder data."""
        # If this is an update, get the existing instance
        instance = self.instance
        application = attrs.get('application', getattr(instance, 'application', None))
        
        # Ensure the reminder time is before the application deadline
        if application and 'reminder_time' in attrs:
            if attrs['reminder_time'] > application.deadline:
                raise serializers.ValidationError({
                    'reminder_time': _(
                        "Reminder time must be before the application deadline."
                    )
                })
        
        return attrs


class CreateReminderSerializer(ReminderSerializer):
    """Serializer for creating reminders with additional validation."""
    
    class Meta(ReminderSerializer.Meta):
        fields = ReminderSerializer.Meta.fields + ['user']
        read_only_fields = [f for f in ReminderSerializer.Meta.read_only_fields if f != 'user']
    
    def validate(self, attrs):
        """Validate the reminder data."""
        attrs = super().validate(attrs)
        request = self.context.get('request')
        
        if request and not attrs.get('user'):
            attrs['user'] = request.user
        
        # Check for duplicate reminders
        if Reminder.objects.filter(
            user=attrs['user'],
            application=attrs['application'],
            reminder_type=attrs.get('reminder_type', Reminder.ReminderType.EMAIL),
            is_sent=False
        ).exists():
            raise serializers.ValidationError({
                'non_field_errors': _(
                    "A similar reminder already exists for this application."
                )
            })
        
        return attrs
