# backend/backend/settings.py
import os

from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 Sécurité
SECRET_KEY = config('DJANGO_SECRET_KEY', default='unsafe-secret-key')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

if not DEBUG:
    ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', cast=Csv(), default=['localhost', '127.0.0.1'])
else:
    ALLOWED_HOSTS = ['*']

# 📦 Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Tiers
    'rest_framework',
    'corsheaders',
    'rest_framework.authtoken',

    # Local
    'api',
]

# 🛡 Middleware nécessaire pour l’admin
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 🌐 Templates (nécessaire pour l’admin)
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

# 📁 Base de données PostgreSQL
import dj_database_url

#if config('DATABASE_URL', default=None):
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'), conn_max_age=600)
}
"""else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB'),
            'USER': config('POSTGRES_USER'),
            'PASSWORD': config('POSTGRES_PASSWORD'),
            'HOST': config('POSTGRES_HOST', default='db'),
            'PORT': config('POSTGRES_PORT', cast=int, default=5432),
        }
    }"""





# 🌍 Langue & fuseau horaire
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# 📁 Fichiers statiques et médias
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 📦 Autres paramètres DRF, CORS, etc.
# backend/settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.CookieTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ]
  
}


# backend/settings.py

# backend/settings.py

AUTH_USER_MODEL = 'api.CustomUser'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py
# Pour le développement (HTTP)
if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    # Pour la production (HTTPS)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"


# CORS configuration pour le développement
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://41.111.227.22:3000",
    "http://41.111.227.22:8000",
    "https://neurev-ia-frontend-eight.vercel.app",
]

# ---------- CSRF ----------
CSRF_TRUSTED_ORIGINS = [
    "https://neurev-ia-frontend-eight.vercel.app",
    "https://neurevia-v1-2.onrender.com",  # ton backend Render
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'backend.urls'

# settings.py
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')  # Pour développement


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '19f9efc72cbfdd'  # Remplacez par le vôtre
EMAIL_HOST_PASSWORD = '4d36cb292ccc58'  # Remplacez par le vôtre
EMAIL_PORT = 2525
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'noreply@neurevia.com'
