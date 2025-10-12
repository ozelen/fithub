"""
API views for the accounts app.
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Accounts"],
        summary="Register a new user",
        description="Create a new user account with username, email, and password",
        responses={
            201: OpenApiResponse(
                description="User created successfully",
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new user account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for user profile management.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Return the current user.
        """
        return self.request.user

    @extend_schema(
        tags=["Accounts"],
        summary="Get user profile",
        description="Retrieve the current user's profile information",
        responses={
            200: OpenApiResponse(
                description="User profile retrieved successfully",
                response=UserProfileSerializer
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve user profile.
        """
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Accounts"],
        summary="Update user profile",
        description="Update the current user's profile information",
        responses={
            200: OpenApiResponse(
                description="Profile updated successfully",
                response=UserUpdateSerializer
            ),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Update user profile.
        """
        serializer = UserUpdateSerializer(
            self.get_object(),
            data=request.data,
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'user': UserProfileSerializer(self.get_object()).data,
            'message': 'Profile updated successfully'
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    tags=["Accounts"],
    summary="Change user password",
    description="Change the current user's password",
    responses={
        200: OpenApiResponse(description="Password changed successfully"),
        400: OpenApiResponse(description="Invalid input data")
    }
)
def change_password(request):
    """
    Change user password.
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    return Response({'message': 'Password changed successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    tags=["Accounts"],
    summary="Delete user account",
    description="Delete the current user's account",
    responses={
        200: OpenApiResponse(description="Account deleted successfully"),
        400: OpenApiResponse(description="Invalid request")
    }
)
def delete_account(request):
    """
    Delete user account.
    """
    user = request.user
    user.delete()
    
    return Response({'message': 'Account deleted successfully'})
