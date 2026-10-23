"""Configuração do app gipe."""

from django.apps import AppConfig


class GipeConfig(AppConfig):
    """Gateway de leitura dos bancos do GIPE para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gipe"
    verbose_name = "GIPE"
