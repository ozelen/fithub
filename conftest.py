"""
Pytest configuration with PostgreSQL test containers.
"""

import pytest
from django.conf import settings
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    """
    Start PostgreSQL test container for the entire test session.
    """
    postgres_container = PostgresContainer("postgres:16")
    postgres_container.start()

    yield postgres_container

    # Clean up
    postgres_container.stop()


@pytest.fixture(scope="session")
def django_db_setup(postgres_container, django_db_blocker):
    """
    Set up Django database using PostgreSQL test container.
    """
    # Get container connection details
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)

    # Update Django settings with container details
    settings.DATABASES["default"].update(
        {
            "HOST": host,
            "PORT": port,
            "NAME": "test_fithub",
            "USER": "postgres",
            "PASSWORD": "postgres",
        }
    )

    # Let Django handle the test database creation
    with django_db_blocker.unblock():
        from django.test.utils import setup_databases, teardown_databases

        db_cfg = setup_databases(verbosity=1, interactive=False)

    yield

    # Clean up test database
    with django_db_blocker.unblock():
        teardown_databases(db_cfg, verbosity=1)


@pytest.fixture(scope="function")
def db_with_migrations(django_db_setup, django_db_blocker):
    """
    Ensure database is set up with migrations for each test.
    """
    with django_db_blocker.unblock():
        from django.core.management import call_command

        call_command("migrate", verbosity=0, interactive=False)

    yield


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db_with_migrations):
    """
    Enable database access for all tests.
    """
    pass


@pytest.fixture
def api_client():
    """
    Create an API client for testing.
    """
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """
    Create an authenticated API client.
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user():
    """
    Create a test user.
    """
    from django.contrib.auth.models import User

    return User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")


@pytest.fixture
def superuser():
    """
    Create a test superuser.
    """
    from django.contrib.auth.models import User

    return User.objects.create_superuser(username="admin", email="admin@example.com", password="adminpass123")
