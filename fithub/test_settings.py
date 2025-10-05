"""
Test settings for FitHub project with PostgreSQL test containers.
"""
import os
from .settings import *

# Override database settings for test containers
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_fithub',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',  # Will be overridden by test container
        'PORT': '5432',       # Will be overridden by test container
        'TEST': {
            'NAME': 'test_fithub',
        }
    }
}

# Disable migrations for faster tests (optional)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None

# MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
DEBUG = False
SECRET_KEY = 'test-secret-key-for-testing-only'

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Disable cache during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable email sending during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Test media settings
MEDIA_ROOT = '/tmp/test_media'

# Disable static files collection during tests
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Test-specific REST Framework settings
REST_FRAMEWORK.update({
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
})
