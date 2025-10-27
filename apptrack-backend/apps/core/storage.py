"""
Custom storage backends for the apptrack project.
"""
import os
import mimetypes
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


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


class MediaStorage(S3Boto3Storage):
    """Custom storage for media files on S3."""

    location = 'media'
    file_overwrite = False
    default_acl = 'private'
    custom_domain = False

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Set content type based on file extension
        content_type = mimetypes.guess_type(name)[0]
        if content_type:
            params['ContentType'] = content_type
        return params


def get_s3_signed_url(key, expires_in=3600):
    """
    Generate a pre-signed URL for an S3 object.

    Args:
        key (str): The S3 object key
        expires_in (int): Expiration time in seconds

    Returns:
        str: Pre-signed URL or None if an error occurs
    """
    import boto3
    from botocore.exceptions import ClientError

    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', None) or None,
        config=boto3.session.Config(signature_version='s3v4')
    )

    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': key
            },
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        print(f"Error generating pre-signed URL: {e}")
        return None
