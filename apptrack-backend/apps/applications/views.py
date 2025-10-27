"""
Views for the applications app.
"""
import os
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.core.permissions import IsOwnerOrReadOnly
from apps.applications.permissions import IsOwner
from .models import Application, Attachment, StatusHistory
from apps.reminders.models import Reminder
from .serializers import (
    ApplicationSerializer,
    ApplicationListSerializer,
    ApplicationStatusUpdateSerializer,
    AttachmentSerializer,
    ReminderSerializer,
    StatusHistorySerializer
)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing job/scholarship applications.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filterset_fields = ['status', 'kind']
    search_fields = ['title', 'organization', 'notes', 'tags']
    ordering_fields = ['deadline', 'applied_date', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return only the applications owned by the current user."""
        return Application.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'update_status':
            return ApplicationStatusUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """Set the owner of the application to the current user."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update the status of an application with an optional note."""
        application = self.get_object()
        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get the timeline of status changes for an application."""
        application = self.get_object()
        history = application.status_history.all().order_by('created_at')
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data)


class AttachmentViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    """
    ViewSet for managing file attachments.
    """
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Return only attachments for the current user's applications."""
        return Attachment.objects.filter(application__owner=self.request.user)

    def perform_create(self, serializer):
        """Set the uploaded_by field to the current user."""
        application_id = self.kwargs.get('application_pk')
        application = get_object_or_404(Application, id=application_id, owner=self.request.user)
        
        file_obj = serializer.validated_data['file']
        file_name = file_obj.name
        file_size = file_obj.size
        file_type = file_name.split('.')[-1].lower()
        
        serializer.save(
            application=application,
            uploaded_by=self.request.user,
            name=file_name,
            file_type=file_type,
            file_size=file_size
        )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, application_pk=None):
        """Generate a signed URL for downloading the file."""
        attachment = self.get_object()
        
        # In a real implementation, you would generate a pre-signed URL here
        # For now, we'll just return the file URL if it exists
        if not attachment.file:
            raise Http404("File not found")
            
        return Response({
            'url': attachment.file.url,
            'name': attachment.name,
            'type': attachment.file_type,
            'size': attachment.file_size
        })


class ReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing application reminders.
    """
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filterset_fields = ['is_sent', 'channel']
    ordering = ['remind_at']

    def get_queryset(self):
        """Return only reminders for the current user's applications."""
        return Reminder.objects.filter(application__owner=self.request.user)

    def perform_create(self, serializer):
        """Set the application and schedule the reminder task."""
        application_id = self.kwargs.get('application_pk')
        application = get_object_or_404(Application, id=application_id, owner=self.request.user)
        
        # In a real implementation, you would schedule a Celery task here
        reminder = serializer.save(application=application)
        
        # For now, we'll just set a flag and store the current time when sent
        # In a real app, this would be handled by the Celery task
        if reminder.remind_at <= timezone.now():
            reminder.is_sent = True
            reminder.sent_at = timezone.now()
            reminder.save()

    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None, application_pk=None):
        """Resend a reminder."""
        reminder = self.get_object()
        
        # In a real implementation, you would schedule a new Celery task here
        reminder.is_sent = False
        reminder.sent_at = None
        reminder.save()
        
        serializer = self.get_serializer(reminder)
        return Response(serializer.data)
