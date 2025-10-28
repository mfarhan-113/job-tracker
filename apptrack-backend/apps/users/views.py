"""
Views for the users app.
"""
from rest_framework import status, permissions
from rest_framework import generics, permissions
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    GenericAPIView
)
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .serializers import UserSerializer, UserCreateSerializer

from . import serializers

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        print("Incoming registration data:", request.data)  # Debug log
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': serializers.UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print("Registration error:", str(e))  # Log the full error
            if hasattr(e, 'detail'):
                print("Error details:", e.detail)  # Log validation errors
            raise


class UserProfileView(RetrieveUpdateAPIView):
    """
    View to retrieve and update user profile.
    """
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenViewBase):
    """ 
    Custom token obtain view that returns user data along with tokens.
    """
    serializer_class = serializers.CustomTokenObtainPairSerializer


class LogoutView(GenericAPIView):
    """
    View to log out a user by blacklisting their refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserSerializer

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"error": _("Invalid or expired refresh token")},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(GenericAPIView):
    """
    View to handle password reset requests.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # In a real implementation, you would send a password reset email here
        # For now, we'll just return a success message
        return Response(
            {"detail": _("Password reset link has been sent to your email if it exists in our system.")},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(GenericAPIView):
    """
    View to handle password reset confirmation.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # In a real implementation, you would validate the token and update the password
        # For now, we'll just return a success message
        return Response(
            {"detail": _("Password has been reset successfully.")},
            status=status.HTTP_200_OK
        )
