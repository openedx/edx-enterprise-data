"""
These settings are here to use during tests, because django requires them.

In a real-world use case, apps in this project are installed into other
Django applications, so these settings will not be used.
"""
from __future__ import absolute_import, unicode_literals

from os.path import abspath, dirname, join

from enterprise_data_roles.constants import (
    ENTERPRISE_DATA_ADMIN_ROLE,
    SYSTEM_ENTERPRISE_ADMIN_ROLE,
    SYSTEM_ENTERPRISE_OPERATOR_ROLE,
)


def here(*args):
    """
    Return the absolute path to a directory from this file.
    """
    return join(abspath(dirname(__file__)), *args)


def root(*args):
    """
    Return the absolute path to some file from the project's root.
    """
    return abspath(join(abspath(here('../..')), *args))


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "default.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.sessions",
    "django.contrib.admin",  # only used in DEBUG mode
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "waffle",

    "enterprise_data",
    "enterprise_reporting",
    "enterprise_data_roles",
    "rules.apps.AutodiscoverRulesConfig",
)

MIDDLEWARE_CLASSES = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "crum.CurrentRequestUserMiddleware",
    "waffle.middleware.WaffleMiddleware",
]

MIDDLEWARE = MIDDLEWARE_CLASSES  # Django 1.10 compatibility - the setting was renamed

AUTHENTICATION_BACKENDS = [
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend"
]

SESSION_ENGINE = "django.contrib.sessions.backends.file"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": {
                "django.contrib.auth.context_processors.auth",  # this is required for admin
                "django.contrib.messages.context_processors.messages",
            }
        }
    },
]

LMS_BASE_URL = "http://localhost:8000/"

ROOT_URLCONF = "enterprise_data.urls"

SECRET_KEY = "insecure-secret-key"

USE_TZ = True
TIME_ZONE = 'UTC'

SITE_NAME = 'analytics-data-api'

# Required for use with edx-drf-extensions JWT functionality:
# USER_SETTINGS overrides for djangorestframework-jwt APISettings class
# See https://github.com/GetBlimp/django-rest-framework-jwt/blob/master/rest_framework_jwt/settings.py
JWT_AUTH = {
    'JWT_AUDIENCE': 'test-aud',
    'JWT_DECODE_HANDLER': 'edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler',
    'JWT_ISSUER': 'test-iss',
    'JWT_LEEWAY': 1,
    'JWT_SECRET_KEY': 'test-key',
    'JWT_SUPPORTED_VERSION': '1.0.0',
    'JWT_VERIFY_AUDIENCE': False,
    'JWT_VERIFY_EXPIRATION': True,

    # JWT_ISSUERS enables token decoding for multiple issuers (Note: This is not a native DRF-JWT field)
    # We use it to allow different values for the 'ISSUER' field, but keep the same SECRET_KEY and
    # AUDIENCE values across all issuers.
    'JWT_ISSUERS': [
        {
            'ISSUER': 'test-issuer-1',
            'SECRET_KEY': 'test-secret-key',
            'AUDIENCE': 'test-audience',
        },
        {
            'ISSUER': 'test-issuer-2',
            'SECRET_KEY': 'test-secret-key',
            'AUDIENCE': 'test-audience',
        }
    ],
}

SYSTEM_TO_FEATURE_ROLE_MAPPING = {
    SYSTEM_ENTERPRISE_ADMIN_ROLE: [ENTERPRISE_DATA_ADMIN_ROLE],
    SYSTEM_ENTERPRISE_OPERATOR_ROLE: [ENTERPRISE_DATA_ADMIN_ROLE],
}
