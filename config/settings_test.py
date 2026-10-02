"""Tests use a disposable Compose database, never the restored catalogue."""
from .settings import *

if os.environ.get('DATABASE_NAME') != 'silentflow_test' or os.environ.get('DATABASE_HOST') != 'database':
    raise ImproperlyConfigured('Run tests with compose.test.yml and its isolated database.')

SECRET_KEY = 'isolated-tests-only'
DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
TEST_RUNNER = 'sf.test_runner.CatalogueTestRunner'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
