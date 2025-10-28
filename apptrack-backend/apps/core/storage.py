"""
Custom storage backends for the apptrack project.
"""
import os
import mimetypes
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# Only import boto3 if AWS settings are available
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def get_file_mimetype(file):
    """Get the MIME type of a file."""
    content_type = mimetypes.guess_type(file.name)[0]
    return content_type or 'application/octet-stream'


def validate_file_extension(file):
    """Validate file extension against allowed file types."""
    allowed_extensions = ['.pdf', '.doc', '.docx', '.odt', '.txt']
    ext = os.path.splitext(file.name)[1].lower()
    return ext in allowed_extensions


def validate_file_size(file, max_size_mb=10):
    """Validate file size."""
    max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
    return file.size <= max_size


class OverwriteStorage(FileSystemStorage):
    """Storage that allows overwriting files with the same name."""

    def get_available_name(self, name, max_length=None):
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            self.delete(name)
        return name


class MediaStorage(FileSystemStorage):
    """Local file system storage for media files."""
    def __init__(self, location=None, base_url=None, file_permissions_mode=None):
        if location is None:
            location = os.path.join(settings.BASE_DIR, 'media')
        if base_url is None:
            base_url = '/media/'
        super().__init__(location=location, base_url=base_url, file_permissions_mode=file_permissions_mode)


def get_file_url(key, expires_in=3600):
    """
    Get a URL for a file, using local filesystem by default.
    For AWS S3, you'll need to set up the appropriate settings.
    """
    # If AWS settings are available, try to generate a pre-signed URL
    if (BOTO3_AVAILABLE and 
        hasattr(settings, 'AWS_ACCESS_KEY_ID') and 
        hasattr(settings, 'AWS_SECRET_ACCESS_KEY') and 
        hasattr(settings, 'AWS_STORAGE_BUCKET_NAME')):
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', None),
                config=boto3.session.Config(signature_version='s3v4')
            )

            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return url
        except (ClientError, Exception) as e:
            print(f"Error generating pre-signed URL, falling back to local URL: {e}")
    
    # Fall back to local file URL
    return f"/media/{key}"