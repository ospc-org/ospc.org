"""
Django settings for webapp project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ['HTTP_X_FORWARDED_PROTO', 'https']

import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'secret key')
SITE_ID = os.environ.get('SITE_ID', 1)

# Allow all host headers
ALLOWED_HOSTS = ['*']

SITE_ID = 1

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/
from django.conf import global_settings

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DEV_DEBUG') == 'True' else False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            (BASE_DIR + '/templates/')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': global_settings.TEMPLATE_CONTEXT_PROCESSORS + [
                'webapp.apps.pages.views.settings_context_processor',
                'webapp.context_processors.google_analytics',
            ],
        },
    },
]


WEBAPP_VERSION = "1.7.2"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Apps
    'webapp.apps.taxbrain',
    'webapp.apps.dynamic',
    'webapp.apps.pages',
    'webapp.apps.register',
    'webapp.apps.btax',

    # Third party apps
    'flatblocks',
    'account',
    'gunicorn',
    'import_export',
    'storages'
]

MIDDLEWARE_CLASSES = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webapp.urls'

WSGI_APPLICATION = 'webapp.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

# if os.environ.get('DATABASE_URL', None):
# Parse database configuration from $DATABASE_URL
TEST_DATABASE = {
    'TEST': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'NAME': 'test_db',
        'PASSWORD': os.environ.get('DATABASE_PW', ''),
    }
}
if os.environ.get('DATABASE_URL', None): # DATABASE_URL var is set
    DATABASES = {'default': dj_database_url.config()}
    DATABASES.update(TEST_DATABASE)
else: # DATABASE_URL is not set--try default
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'taxcalc',
            'USER': os.environ.get('DATABASE_USER', 'postgres'),
            'PASSWORD': os.environ.get('DATABASE_PW', ''),
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    DATABASES.update(TEST_DATABASE)


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Use whitenoise to serve static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
SENDGRID_API_KEY=os.environ.get("SENDGRID_API_KEY", "not-specified")
EMAIL_BACKEND = "sgbackend.SendGridBackend"
BLOG_URL = os.environ.get('BLOG_URL', 'http://news.ospc.org/')

GOOGLE_ANALYTICS_PROPERTY_ID = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", "")
GOOGLE_ANALYTICS_EMBEDDED_ID = os.environ.get("GOOGLE_ANALYTICS_EMBEDDED_ID", "")
GOOGLE_ANALYTICS_DOMAIN = os.environ.get("GOOGLE_ANALYTICS_DOMAIN", "")
