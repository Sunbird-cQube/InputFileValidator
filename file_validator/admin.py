from django.contrib import admin

from file_validator.models import *

# Register your models here.
admin.site.register(Profile)
admin.site.register(ValidationError)
admin.site.register(CustomValidationError)
