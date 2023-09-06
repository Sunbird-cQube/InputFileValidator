from django.contrib.auth.views import LoginView
from django.contrib import admin
from django.urls import path, include
from .views import *


urlpatterns = [
    path('',  home, name="home"),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('register', register_attempt, name="register_attempt"),
    path('index', index_page, name='index'),
    path('accounts/login/', login_attempt, name="login_attempt"),
    path('token', token_send, name="token_send"),
    path('success', success, name='success'),
    path('verify/<auth_token>', verify, name="verify"),
    path('error', error_page, name="error"),
    path('forgot', forgot, name="forgot"),
    path('reset/<auth_token>', reset, name="reset"),
    # path("search_tags/", search_tags, name="search_tags"),
    path("logout/", logout_view, name="logout_view"),
    path('accounts/login/', LoginView.as_view(template_name='login.html'), name='login'),

]
