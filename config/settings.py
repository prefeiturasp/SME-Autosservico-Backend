"""Configurações do projeto SME Autosservico Backend.

Arquivo único, lendo todos os valores variáveis do ambiente, conforme o
padrão SME para aplicações Python + Django.
"""

import sys
from pathlib import Path
from typing import Any

import environ

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
APPS_DIR = BASE_DIR / "apps"

env = environ.Env()

# Lê o arquivo .env automaticamente quando ele existir (silenciosamente
# ignorado se ausente — por exemplo, em produção, onde as variáveis vêm
# diretamente do ambiente do container).
env.read_env(str(BASE_DIR / ".env"))

DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Detecta execução da suíte de testes para habilitar defaults seguros
# (SECRET_KEY, hosts e banco de dados) independente de DEBUG/.env.
RUNNING_TESTS = "pytest" in sys.modules or "test" in sys.argv

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-change-me" if DEBUG or RUNNING_TESTS else None,
)
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=(
        ["localhost", "127.0.0.1", "0.0.0.0"]  # noqa: S104
        if DEBUG or RUNNING_TESTS
        else []
    ),
)

TIME_ZONE = "America/Sao_Paulo"
LANGUAGE_CODE = "pt-br"
USE_I18N = True
USE_TZ = True

# Banco de dados
# Durante os testes usa SQLite em memória (rápido e isolado). Fora dos
# testes, usa um arquivo SQLite local por padrão — trocável para Postgres
# (ou outro backend) via DATABASE_URL assim que houver persistência
# definida para este serviço.
DATABASES: dict[str, dict[str, Any]]
if RUNNING_TESTS:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")
    }
DATABASES["default"]["ATOMIC_REQUESTS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
]
LOCAL_APPS = [
    "apps.core",
    "apps.sigpae",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

if DEBUG:
    INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]
if RUNNING_TESTS:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATIC_URL = "/static/"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")
# Nenhum ADMINS/MANAGERS específico configurado ainda; conectar via
# variáveis de ambiente quando houver alerta por e-mail.
ADMINS: list = []
MANAGERS = ADMINS

# Autenticação por API Key (padrão SME para microsserviços) — ver
# apps/core/authentication.py.
API_KEY = env("API_KEY", default="")
API_KEY_HEADER = env("API_KEY_HEADER", default="X-Api-Key")

# Connection string somente-leitura do banco do SIGPAE. Deve incluir
# connect_timeout e sslmode=prefer (o servidor não suporta SSL).
SIGPAE_DSN = env("SIGPAE_DSN", default="")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.core.authentication.ApiKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOWED_ORIGINS = env.list(
    "DJANGO_CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"]
)

SPECTACULAR_SETTINGS: dict[str, Any] = {
    "TITLE": "SME Autosservico Backend API",
    "DESCRIPTION": "Documentação dos endpoints da API do SME Autosservico Backend.",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "SCHEMA_PATH_PREFIX": "/api/v1/",
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": API_KEY_HEADER,
            },
        },
    },
    "SECURITY": [{"ApiKeyAuth": []}],
}

if not DEBUG and not RUNNING_TESTS:
    CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=518400)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
    )
    SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
