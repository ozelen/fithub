"""
Web-based authentication views for frontend applications.
"""

import json

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import UserProfileSerializer, UserRegistrationSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
@extend_schema(
    tags=["Web Authentication"],
    summary="Web user registration",
    description="Register a new user account via web interface",
    responses={
        201: OpenApiResponse(description="User created successfully"),
        400: OpenApiResponse(description="Invalid input data"),
    },
)
def web_register(request):
    """
    Web-based user registration endpoint.
    """
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, bytes)
            else request.data
        )
    except (json.JSONDecodeError, AttributeError):
        data = request.data

    serializer = UserRegistrationSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()

        # Auto-login the user after registration
        login(request, user)

        return Response(
            {
                "success": True,
                "message": "User registered successfully",
                "user": UserProfileSerializer(user).data,
                "redirect_url": "/dashboard/",  # Frontend redirect
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"success": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@extend_schema(
    tags=["Web Authentication"],
    summary="Web user login",
    description="Login user via web interface",
    responses={
        200: OpenApiResponse(description="Login successful"),
        401: OpenApiResponse(description="Invalid credentials"),
    },
)
def web_login(request):
    """
    Web-based user login endpoint.
    """
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, bytes)
            else request.data
        )
    except (json.JSONDecodeError, AttributeError):
        data = request.data

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return Response(
            {"success": False, "error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)

    if user is not None:
        if user.is_active:
            login(request, user)
            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "user": UserProfileSerializer(user).data,
                    "redirect_url": "/dashboard/",
                }
            )
        else:
            return Response(
                {"success": False, "error": "Account is disabled"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    else:
        return Response(
            {"success": False, "error": "Invalid username or password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@extend_schema(
    tags=["Web Authentication"],
    summary="Web user logout",
    description="Logout user via web interface",
    responses={200: OpenApiResponse(description="Logout successful")},
)
def web_logout(request):
    """
    Web-based user logout endpoint.
    """
    logout(request)
    return Response(
        {"success": True, "message": "Logout successful", "redirect_url": "/"}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@extend_schema(
    tags=["Web Authentication"],
    summary="Get current user info",
    description="Get current authenticated user information",
    responses={
        200: OpenApiResponse(description="User info retrieved successfully")
    },
)
def web_user_info(request):
    """
    Get current user information for web interface.
    """
    return Response(
        {
            "success": True,
            "user": UserProfileSerializer(request.user).data,
            "is_authenticated": True,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@extend_schema(
    tags=["Web Authentication"],
    summary="Check authentication status",
    description="Check if user is authenticated",
    responses={
        200: OpenApiResponse(description="Authentication status checked")
    },
)
def web_auth_status(request):
    """
    Check authentication status for web interface.
    """
    if request.user.is_authenticated:
        return Response(
            {
                "success": True,
                "is_authenticated": True,
                "user": UserProfileSerializer(request.user).data,
            }
        )
    else:
        return Response(
            {"success": True, "is_authenticated": False, "user": None}
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@extend_schema(
    tags=["Web Authentication"],
    summary="Update user profile",
    description="Update user profile via web interface",
    responses={
        200: OpenApiResponse(description="Profile updated successfully"),
        400: OpenApiResponse(description="Invalid input data"),
    },
)
def web_update_profile(request):
    """
    Update user profile for web interface.
    """
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, bytes)
            else request.data
        )
    except (json.JSONDecodeError, AttributeError):
        data = request.data

    user = request.user

    # Update allowed fields
    allowed_fields = ["email", "first_name", "last_name"]
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    try:
        user.save()
        return Response(
            {
                "success": True,
                "message": "Profile updated successfully",
                "user": UserProfileSerializer(user).data,
            }
        )
    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Template-based views for serving HTML pages
def login_page(request):
    """
    Serve the login page.
    """
    return render(request, "accounts/login.html")


def register_page(request):
    """
    Serve the registration page.
    """
    return render(request, "accounts/register.html")
