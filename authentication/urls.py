"""
URL configuration for authentication endpoints.
"""

from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import CustomObtainAuthToken


class TaggedTokenObtainPairView(TokenObtainPairView):
    @extend_schema(
        tags=["Authentication"],
        summary="Obtain JWT tokens",
        description="Get JWT access and refresh tokens using username and password",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TaggedTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Authentication"],
        summary="Refresh JWT token",
        description="Refresh JWT access token using refresh token",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TaggedTokenVerifyView(TokenVerifyView):
    @extend_schema(
        tags=["Authentication"],
        summary="Verify JWT token",
        description="Verify if a JWT token is valid",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


urlpatterns = [
    # Token Authentication (DRF Token)
    path("token/", CustomObtainAuthToken.as_view(), name="api_token_auth"),
    # JWT Authentication
    path(
        "jwt/token/",
        TaggedTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "jwt/token/refresh/",
        TaggedTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "jwt/token/verify/",
        TaggedTokenVerifyView.as_view(),
        name="token_verify",
    ),
]
