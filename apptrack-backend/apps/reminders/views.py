"""
Views for the reminders app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from apps.reminders.models import Reminder
from apps.reminders.serializers import (
    ReminderSerializer,
    CreateReminderSerializer,
)
from apps.utils.permissions import IsOwnerOrReadOnly


class ReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reminders to be viewed or edited.
    """
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Return only the reminders for the current user."""
        return Reminder.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action in ['create', 'update', 'partial_update']:
            return CreateReminderSerializer
        return ReminderSerializer
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating a reminder."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """
        Resend a reminder that has already been sent.
        """
        reminder = self.get_object()
        
        # Check if the reminder was already sent
        if not reminder.is_sent:
            return Response(
                {'detail': _('This reminder has not been sent yet.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a new reminder with the same data
        new_reminder = Reminder.objects.create(
            user=reminder.user,
            application=reminder.application,
            reminder_type=reminder.reminder_type,
            reminder_time=reminder.reminder_time,
        )
        
        # Queue the reminder to be sent
        from apps.reminders.tasks import send_reminder_email
        send_reminder_email.delay(new_reminder.id)
        
        serializer = self.get_serializer(new_reminder)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming reminders for the current user.
        """
        from django.utils import timezone
        
        reminders = Reminder.objects.filter(
            user=request.user,
            is_sent=False,
            reminder_time__gte=timezone.now()
        ).order_by('reminder_time')
        
        page = self.paginate_queryset(reminders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)
