"""Configuração do app sgp."""

from django.apps import AppConfig


class SgpConfig(AppConfig):
    """Gateway de leitura do banco do SGP para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sgp"
    verbose_name = "SGP"
