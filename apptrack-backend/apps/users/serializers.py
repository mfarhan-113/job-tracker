"""
Serializers for the users app.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'timezone', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Confirm Password'}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        print("Validating user data:", attrs)  # Debug log
        if attrs['password'] != attrs.pop('password_confirm'):
            print("Password mismatch error")  # Debug log
            raise serializers.ValidationError({"password": _("Password fields didn't match.")})
        print("Validation passed")  # Debug log
        return attrs

    def create(self, validated_data):
        print("Creating user with data:", validated_data)  # Debug log
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm', None)
        try:
            user = User.objects.create_user(**validated_data)
            print("User created successfully:", user)  # Debug log
            return user
        except Exception as e:
            print("Error creating user:", str(e))  # Debug log
            raise


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'timezone')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token obtain serializer that supports both email and username login
    and includes user data in the response.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField(required=False)
    
    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')
        
        # If email is provided, find the username
        if email and not username:
            try:
                user = User.objects.get(email=email)
                attrs['username'] = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'detail': 'No active account found with the given credentials'
                })
        
        # If neither email nor username is provided
        elif not username:
            raise serializers.ValidationError({
                'detail': 'Must include either username or email and password.'
            })
            
        # Standard validation
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        
        # Add custom claims
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = UserSerializer(self.user).data
        
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    password = serializers.CharField(required=True)
    password_confirm = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    uidb64 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": _("Password fields didn't match.")})
        return attrs
