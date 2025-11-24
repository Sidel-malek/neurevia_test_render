import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------
# SECURITY
# -------------------------------------------------------
SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-secret-key")
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = ["*"]

# -------------------------------------------------------
# APPS
# -------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",

    "api",
]

# -------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # Si tu as des templates personnalisés, mets leur chemin ici
        "APP_DIRS": True,  # 🔥 crucial : permet à Django de chercher dans les apps, y compris admin
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

# -------------------------------------------------------
# DATABASE
# -------------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(config("DATABASE_URL"), conn_max_age=600)
}

# -------------------------------------------------------
# STATIC & MEDIA
# -------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------
# DRF
# -------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "authentication.CookieTokenAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
}

AUTH_USER_MODEL = "api.CustomUser"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------
# COOKIES CONFIG (Render ↔ Render)
# -------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

# CRITICAL: Doit être None pour Render
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# Add max age
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days

# -------------------------------------------------------
# CORS CONFIG
# -------------------------------------------------------
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://neurevia-frontend.onrender.com",        # Frontend Render
]

# -------------------------------------------------------
# CSRF TRUSTED ORIGINS
# -------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://neurevia-frontend.onrender.com",        # Frontend
    "https://neurevia-test-render.onrender.com",     # Backend
]

# -------------------------------------------------------
# EMAIL SMTP
# -------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "sandbox.smtp.mailtrap.io"
EMAIL_HOST_USER = "19f9efc72cbfdd"
EMAIL_HOST_PASSWORD = "4d36cb292ccc58"
EMAIL_PORT = 2525
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "noreply@neurevia.com"