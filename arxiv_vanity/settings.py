"""
For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from django.core.exceptions import ImproperlyConfigured
import environ

env = environ.Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', 'web'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'raven.contrib.django.raven_compat',
    'arxiv_vanity.papers',
    'arxiv_vanity.scraper',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'arxiv_vanity.urls'
APPEND_SLASH = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'arxiv_vanity/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'arxiv_vanity.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default='psql://postgres@db:5432/postgres'),
}
DATABASES['default'].update({
    'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',
    'ATOMIC_REQUESTS': False,
    'CONN_MAX_AGE': 0,
    'OPTIONS': {
        'MAX_CONNS': env.int('DATABASE_MAX_CONNS', default=4)
    }
})

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = '/'
# LOGIN_URL = '/login/'

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "arxiv_vanity/static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "arxiv_vanity/static_root")

# Uploaded files, including paper source and rendered articles
MEDIA_USE_S3 = env.bool('MEDIA_USE_S3', default=False)
if MEDIA_USE_S3:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME')
    MEDIA_URL = env('MEDIA_URL', default=f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/')
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    MEDIA_URL = '/media/'

# Log everything to the console, including tracebacks
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console', 'sentry'],
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': 'x'},
        },
        'console': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'class': 'logging.StreamHandler',
        },
    },
}

# SSL
ENABLE_SSL = env.bool('ENABLE_SSL', default=False)
SESSION_COOKIE_SECURE = ENABLE_SSL
CSRF_COOKIE_SECURE = ENABLE_SSL
# SECURE_SSL_REDIRECT = ENABLE_SSL
if ENABLE_SSL:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Paper rendering
# HACK: If image is set to blank string in environment, resolve default.
# django-environ's defaults only work if envvar is actually unset
ENGRAFO_IMAGE = env('ENGRAFO_IMAGE', default='') or 'engrafo:latest'
ENGRAFO_USE_HYPER_SH = env.bool('ENGRAFO_USE_HYPER_SH', default=False)
if ENGRAFO_USE_HYPER_SH:
    if not MEDIA_USE_S3:
        raise ImproperlyConfigured('When the setting ENGRAFO_USE_HYPER_SH is True, MEDIA_USE_S3 must also be True.')
    HYPER_ACCESS_KEY = env('HYPER_ACCESS_KEY')
    HYPER_SECRET_KEY = env('HYPER_SECRET_KEY')
    HYPER_ENDPOINT = env('HYPER_ENDPOINT', default='https://us-west-1.hyper.sh:443/v1.23')
    # https://hyper.sh/pricing.html
    # m1 = 1 GB RAM
    HYPER_INSTANCE_TYPE = env('HYPER_INSTANCE_TYPE', default='m1')
# The prefix to use for Engrafo webhooks
ENGRAFO_WEBHOOK_URL_PREFIX = env('ENGRAFO_WEBHOOK_URL_PREFIX', default='http://web:8000')

# Papers
PAPERS_MACHINE_LEARNING_CATEGORIES = [
    "cs.CV",
    "cs.AI",
    "cs.LG",
    "cs.CL",
    "cs.NE",
    "stat.ML"
]

# Number of days after which to re-render papers
PAPERS_EXPIRED_DAYS = env.int('PAPERS_EXPIRED_DAYS', default=7)
