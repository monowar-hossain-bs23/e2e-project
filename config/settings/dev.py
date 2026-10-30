"""Development Django settings for Basha Pass."""

from config.settings.base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]", "testserver"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
