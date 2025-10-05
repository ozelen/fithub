"""
Tests for authentication API endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class AuthenticationAPITestCase(APITestCase):
    """Test cases for authentication API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_token_authentication_success(self):
        """Test successful token authentication."""
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user_id", response.data)
        self.assertIn("username", response.data)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["user_id"], self.user.id)

    def test_token_authentication_invalid_credentials(self):
        """Test token authentication with invalid credentials."""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_authentication_missing_credentials(self):
        """Test token authentication with missing credentials."""
        data = {
            "username": "testuser"
            # Missing password
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_authentication_nonexistent_user(self):
        """Test token authentication with nonexistent user."""
        data = {
            "username": "nonexistent",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_authentication_returns_user_info(self):
        """Test that token authentication returns complete user information."""
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = ["token", "user_id", "username", "email", "is_staff", "is_superuser"]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_token_authentication_creates_token(self):
        """Test that token authentication creates a new token."""
        # Ensure no token exists initially
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)
        
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)
        
        # Verify the token is valid
        token = Token.objects.get(user=self.user)
        self.assertEqual(response.data["token"], token.key)

    def test_token_authentication_reuses_existing_token(self):
        """Test that token authentication reuses existing token."""
        # Create an existing token
        existing_token = Token.objects.create(user=self.user)
        
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], existing_token.key)
        # Should still have only one token
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_authenticated_request_with_token(self):
        """Test that authenticated requests work with the token."""
        # Get a token
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/token/", data)
        token = response.data["token"]
        
        # Use token for authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get("/api/nutrition/diets/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_request_fails(self):
        """Test that unauthenticated requests fail."""
        response = self.client.get("/api/nutrition/diets/")
        # JWT authentication returns 401, Token authentication returns 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class JWTAuthenticationAPITestCase(APITestCase):
    """Test cases for JWT authentication API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_jwt_token_obtain_success(self):
        """Test successful JWT token obtain."""
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/jwt/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_jwt_token_obtain_invalid_credentials(self):
        """Test JWT token obtain with invalid credentials."""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post("/api/auth/jwt/token/", data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_refresh_success(self):
        """Test successful JWT token refresh."""
        # First get tokens
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/jwt/token/", data)
        refresh_token = response.data["refresh"]
        
        # Refresh the token
        refresh_data = {"refresh": refresh_token}
        response = self.client.post("/api/auth/jwt/token/refresh/", refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_jwt_token_verify_success(self):
        """Test successful JWT token verification."""
        # First get tokens
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/jwt/token/", data)
        access_token = response.data["access"]
        
        # Verify the token
        verify_data = {"token": access_token}
        response = self.client.post("/api/auth/jwt/token/verify/", verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jwt_token_verify_invalid_token(self):
        """Test JWT token verification with invalid token."""
        verify_data = {"token": "invalid_token"}
        response = self.client.post("/api/auth/jwt/token/verify/", verify_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_request_with_jwt(self):
        """Test that authenticated requests work with JWT."""
        # Get JWT tokens
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/api/auth/jwt/token/", data)
        access_token = response.data["access"]
        
        # Use JWT for authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get("/api/nutrition/diets/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jwt_token_refresh_invalid_token(self):
        """Test JWT token refresh with invalid refresh token."""
        refresh_data = {"refresh": "invalid_refresh_token"}
        response = self.client.post("/api/auth/jwt/token/refresh/", refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
