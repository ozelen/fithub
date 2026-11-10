import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

KEY = ec.generate_private_key(ec.SECP256R1())
PUB = KEY.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
URL = "/api/plan/activity-types/"


def token(key=KEY, **claims):
    payload = {"iss": "https://app.zelen.uk", "aud": "fit", "exp": 9999999999, "email": "o@zelen.uk", **claims}
    return jwt.encode(payload, key, algorithm="ES256")


def get(tok):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}")
    return client.get(URL)


@pytest.fixture(autouse=True)
def public_key(settings):
    settings.APP_JWT_PUBLIC_KEY = PUB


@pytest.mark.django_db
def test_app_token_maps_email_to_user_and_creates_unknown_ones():
    user = get_user_model().objects.create_user("ozelen", email="o@zelen.uk", password="x")
    r = get(token())
    assert r.status_code == 200 and r.wsgi_request.user == user
    assert get(token(email="friend@example.com")).status_code == 200
    assert get_user_model().objects.filter(username="friend@example.com").exists()


@pytest.mark.django_db
def test_app_token_rejects_wrong_audience_key_and_issuer():
    assert get(token(aud="fin")).status_code == 401
    assert get(token(key=ec.generate_private_key(ec.SECP256R1()))).status_code == 401
    assert get(token(iss="https://elsewhere")).status_code == 401  # falls through to simplejwt
