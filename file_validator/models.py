import os
from django.db import models

# Create your models here.
from django.contrib.auth.models import User

from file_validator_app.settings import MEDIA_ROOT


def user_directory_path(self, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(self.creator.username, filename)


def user_directory_path_file(self, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(self.publisher, filename)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class ValidationError(models.Model):
    error_type = models.CharField(max_length=255, null=True)
    error_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.error_type} - Count: {self.error_count}"


class CustomValidationError(models.Model):
    error_type = models.CharField(max_length=255, null=True)
    error_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.error_type} - Count: {self.error_count}"
