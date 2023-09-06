"""file_validator_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from django.urls import re_path as url
from file_validator import views

urlpatterns = [
    path('', include('file_validator.urls')),
    path('admin/', admin.site.urls),
    url(r'^custom-validation/$', views.custom_validation),
    url(r'^instructions/$', views.instructions),
    url(r'^upload_errors/$', views.upload_errors, name='upload_errors'),
    url(r'^download/$', views.download, name='download'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
