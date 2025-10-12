"""
API URL configuration for the accounts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import (
    UserRegistrationView,
    UserProfileView,
    change_password,
    delete_account,
)

router = DefaultRouter()

urlpatterns = [
    # User registration
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    
    # User profile management
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    
    # Password management
    path("change-password/", change_password, name="change-password"),
    
    # Account management
    path("delete/", delete_account, name="delete-account"),
    
    # Include router URLs
    path("", include(router.urls)),
]
