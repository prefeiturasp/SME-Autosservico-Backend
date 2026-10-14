"""Configuração do app sigpae."""

from django.apps import AppConfig


class SigpaeConfig(AppConfig):
    """Gateway de leitura do banco do SIGPAE para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sigpae"
    verbose_name = "SIGPAE"
