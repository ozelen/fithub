"""Bearer tokens minted by app.zelen.uk for its users (ES256, public key in APP_JWT_PUBLIC_KEY, audience APP_AUDIENCE)."""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions


class AppTokenAuthentication(authentication.BaseAuthentication):
    def authenticate_header(self, request):
        return 'Bearer realm="api"'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if len(header) != 2 or header[0].lower() != b"bearer" or not settings.APP_JWT_PUBLIC_KEY:
            return None
        token = header[1].decode()
        try:
            if jwt.decode(token, options={"verify_signature": False}).get("iss") != settings.APP_ISSUER:
                return None  # not ours; let simplejwt try
            claims = jwt.decode(
                token, settings.APP_JWT_PUBLIC_KEY, algorithms=["ES256"],
                issuer=settings.APP_ISSUER, audience=settings.APP_AUDIENCE,
            )
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed(str(exc)) from exc
        email = claims.get("email") or ""
        if not email:
            raise exceptions.AuthenticationFailed("token has no email")
        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        if user is None:
            user, _ = user_model.objects.get_or_create(username=email.lower(), defaults={"email": email})
        return (user, token)
