"""
Web URL configuration for the accounts app.
"""

from django.urls import path
from .web_views import (
    web_register,
    web_login,
    web_logout,
    web_user_info,
    web_auth_status,
    web_update_profile,
    login_page,
    register_page,
)

urlpatterns = [
    # Template-based pages
    path("signup/", register_page, name="signup-page"),
    path("signin/", login_page, name="login-page"),
    
    # Web authentication API endpoints
    path("register/", web_register, name="web-register"),
    path("login/", web_login, name="web-login"),
    path("logout/", web_logout, name="web-logout"),
    path("user-info/", web_user_info, name="web-user-info"),
    path("auth-status/", web_auth_status, name="web-auth-status"),
    path("update-profile/", web_update_profile, name="web-update-profile"),
]
