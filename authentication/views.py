"""
Custom authentication views for FitHub API.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


class CustomObtainAuthToken(ObtainAuthToken):
    """
    Custom authentication view that returns user information along with the token.
    """

    @extend_schema(
        tags=["Authentication"],
        summary="Obtain authentication token",
        description="Get a DRF authentication token using username and password",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "user_id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "is_staff": {"type": "boolean"},
                    "is_superuser": {"type": "boolean"},
                },
            }
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        )
