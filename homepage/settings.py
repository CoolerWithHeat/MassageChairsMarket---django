from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-g1y((h-*4((b*b8_&cu492+7nj#$@vshr!&rmmt%g&l3t0ssy+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'soothestore',
    'algoliasearch_django',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

CORS_ALLOW_ALL_ORIGINS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'homepage.urls'
AUTH_USER_MODEL = 'soothestore.CustomUser'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'homepage.wsgi.application'


AWS_ACCESS_KEY_ID = 'AKIAW3MEF3JZF2EYIWT5'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'massagechairs'
AWS_S3_REGION_NAME = 'eu-north-1'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_QUERYSTRING_AUTH = False

STRIPE_SECRET_KEY = 'sk_test_51P4rPa03nbzcvY4RdeScMeQRSFlpxB0p8RnJLKoYxeIOY7X3DmpTeE4lThvmxSW5gDadb8C5TMbkBF7xuW5x7hLn00k8XkcwG5'

ALGOLIA = {
    'APPLICATION_ID': 'K7LWE7RYA4',
    'API_KEY': 'dd84d643cb097b484b87bf0a2c35d742'
}

GEOIP_PATH = os.path.join(BASE_DIR, 'GetLite2', 'GeoLite2-City.mmdb')

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_DIRS = [
    BASE_DIR / 'soothestore/templates/homePage-design/assets',
]