import os
from pathlib import Path

# Base directory path
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8s!hb(j^pv$4jk+g7i#wbk%4_u=lkzrsgo+9xtno(*2j2m76b+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # Change this when moving to production

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # Static files app
    'accounts',  # Your custom app
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

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # This looks for templates in the templates folder
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

WSGI_APPLICATION = 'myproject.wsgi.application'

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',  # Your database name
        'USER': 'myuser',  # Your database user
        'PASSWORD': 'zeesh1906',  # Your database password
        'HOST': 'localhost',  # Database host
        'PORT': '5432',  # Database port
    }
}

# Password validation settings
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

# Internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'  # URL for serving static files

# Use this for collecting static files in production
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Add static folder
]

# Directory for collected static files in production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# --- SESSION CONFIGURATION FOR LOGOUT ON BROWSER CLOSE ---
# If True, the session cookie expires when the user closes their browser.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Ensures session data is saved on every request, which is helpful when 
# modifying session expiration logic like this.
SESSION_SAVE_EVERY_REQUEST = True
# -----------------------------------------------------------

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Login redirect URL after successful login
LOGIN_REDIRECT_URL = '/home/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configure for file handling (if required)
MEDIA_URL = '/media/'  # URL for accessing media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Directory for storing media files
