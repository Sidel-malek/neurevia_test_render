import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ⛑ SECURITY
SECRET_KEY = config('DJANGO_SECRET_KEY', default='unsafe-secret-key')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = [
    '*',  # أثناء التطوير على Render
]

# 📦 Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    'api',
]

# 🛡 Middleware
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

ROOT_URLCONF = 'backend.urls'

# 🗃 Database
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'), conn_max_age=600)
}

# 🌍 Locale
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True

# 📁 Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🔐 DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.CookieTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# 👤 User model
AUTH_USER_MODEL = 'api.CustomUser'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 🍪 COOKIES CROSS-DOMAIN (مهم جداً)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Django admin يحتاج CSRF على جافاسكربت

# 🌐 CORS (الفرونت)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://neurev-ia-frontend-eight.vercel.app",
    "https://neurevia-frontend.onrender.com",
]

# 🛡 CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://neurev-ia-frontend-eight.vercel.app",
    "https://neurevia-frontend.onrender.com",
    "https://neurevia-v1-2.onrender.com",
]

# 📧 Email SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = '19f9efc72cbfdd'
EMAIL_HOST_PASSWORD = '4d36cb292ccc58'
EMAIL_PORT = 2525
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@neurevia.com'
