import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-g_n2+2bznu6e@1wel!i(&-4tp86_7lop5395ww+i4x%9*7^old'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []  

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'phonenumber_field',
    'crispy_forms',
    'crispy_bootstrap5',
    'imagekit',
    'django_extensions',
    'django_filters',
    'django_tables2',

    'store.apps.StoreConfig',
    'accounts.apps.AccountsConfig',
    'transactions.apps.TransactionsConfig',
    'invoice.apps.InvoiceConfig',
    'bills.apps.BillsConfig',
    'corsheaders',  
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'accounts.middleware.SessionMiddleware'  
]

ROOT_URLCONF = 'InventoryMS.urls'

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

WSGI_APPLICATION = 'InventoryMS.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation

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


# Internationalization


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LOGIN_URL = 'user-login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_URL = 'logout'

# Static files (CSS, JavaScript, Images)


STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR,'static')
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'static/images')
MEDIA_URL = '/images/'
STATIC_ROOT = BASE_DIR/'static_collect'

# Default primary key field type


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#CSP Settings
SECURE_CSP={
    'script-src': (
        "'self'",
        "'unsafe-inline'",
        "'unsafe-eval'",
       
    ),
    'style-src':(
        "'self'",
        "'unsafe-inline'",
       
    ),
    'default':(
        "'self'",
        "data:",
    ),
    'frame-src':(
        "'self'",
        "*",
    ),
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
 
X_FRAME_OPTIONS='ALLOWALL'
 
 
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000', 
    'http://localhost:8001',     
    "null",  
    "http://localhost:8080"
]
CORS_ALLOW_METHODS=[
    'GET',
    'POST',
    'PUT',
    'OPTIONS',
]
CORS_ALLOW_HEADERS=[
    'Content-Type',
    'Authorization',
]

CORS_ALLOW_CREDENTIALS = True 
CSRF_USE_SAMESITE_COOKIE = False
ALLOWED_HOSTS=['localhost','127.0.0.1']
 
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
SESSION_COOKIE_HTTPONLY="False"  
SECURE_CONTENT_TYPE_NOSNIFF ="False"   

SESSION_SAVE_EVERY_REQUEST=False
SESSION_COOKIE_HTTPONLY=False
SESSION_EXPIRE_AT_BROWSER_CLOSE=False  
 