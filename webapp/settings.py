"""
Django settings for webapp project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'secret key')
SITE_ID = os.environ.get('SITE_ID', 1)

# Allow all host headers
ALLOWED_HOSTS = ['*']

SITE_ID = 1

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import dj_database_url
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DEV_DEBUG') == 'True' else False

TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIRS = (
    (BASE_DIR + '/templates/'),
)

from django.conf import global_settings

WEBAPP_VERSION = "1.2.1"

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'webapp.apps.pages.views.settings_context_processor',
    'webapp.context_processors.google_analytics',
)

# Application definition

INSTALLED_APPS = (
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
    'hermes',
    'import_export',
    'storages'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webapp.urls'

WSGI_APPLICATION = 'webapp.wsgi.application'

CELERY_RESULT_BACKEND = os.environ.get('REDISGREEN_URL')

BROKER_URL = os.environ.get('REDISGREEN_URL')


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

if os.environ.get('DATABASE_URL', None):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'taxcalc',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    # Parse database configuration from $DATABASE_URL
    import dj_database_url
    DATABASES['default'] = dj_database_url.config()
else:
    DATABASES = {
        'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

# AWS S3 static file storage

# Use Amazon S3 for storage for uploaded media files.
DEFAULT_FILE_STORAGE = "storages.backends.s3boto.S3BotoStorage"

# Amazon S3 settings.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ID", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_HOST = os.environ.get("AWS_S3_HOST", None)

# Tell django-storages that when coming up with the URL for an item in S3 storage, keep
# it simple - just use this domain plus the path. (If this isn't set, things get complicated).
# This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
# We also use it in the next setting.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# This is used by the `static` template tag from `static`, if you're using that. Or if anything else
# refers directly to STATIC_URL. So it's safest to always set it.

# STATIC_URL is used by StaticFilesStorage to create the path to static assets when
# using the 'static' template tag. In production, we use storages, so just leave this as
# '/static/' for development purposes
#STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
STATIC_URL = '/static/'

# Tell the staticfiles app to use S3Boto storage when writing the collected static files (when
# you run `collectstatic`).
if True:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

SENDGRID_API_KEY=os.environ.get("SENDGRID_API_KEY", "")
EMAIL_BACKEND = "sgbackend.SendGridBackend"
BLOG_URL = os.environ.get('BLOG_URL', 'http://news.ospc.org/')

GOOGLE_ANALYTICS_PROPERTY_ID = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", "")
GOOGLE_ANALYTICS_EMBEDDED_ID = os.environ.get("GOOGLE_ANALYTICS_EMBEDDED_ID", "")
GOOGLE_ANALYTICS_DOMAIN = os.environ.get("GOOGLE_ANALYTICS_DOMAIN", "")
