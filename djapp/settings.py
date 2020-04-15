import os
import dj_database_url

DEBUG = os.environ.get("DEBUG").lower() == "false"
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgis://openstates:openstates@db:5432/openstatesorg"
)

DATABASES = {"default": {dj_database_url.parse(DATABASE_URL)}}

SECRET_KEY = "not-used"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["geo"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "djapp.urls"
WSGI_APPLICATION = "djapp.wsgi.application"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_L10N = False
USE_TZ = True
STATIC_URL = "/static/"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ]
#         },
#     }
# ]
