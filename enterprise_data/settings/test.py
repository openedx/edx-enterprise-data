"""
These settings are here to use during tests, because django requires them.

In a real-world use case, apps in this project are installed into other
Django applications, so these settings will not be used.
"""
from __future__ import absolute_import, unicode_literals

from os.path import abspath, dirname, join


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

    "enterprise_data",
    "enterprise_reporting"
)

MIDDLEWARE_CLASSES = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

MIDDLEWARE = MIDDLEWARE_CLASSES  # Django 1.10 compatibility - the setting was renamed

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

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
