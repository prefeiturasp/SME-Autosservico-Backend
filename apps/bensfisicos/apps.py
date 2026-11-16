"""Configuração do app bensfisicos."""

from django.apps import AppConfig


class BensFisicosConfig(AppConfig):
    """Gateway de leitura do banco do Bens Físicos para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bensfisicos"
    verbose_name = "Bens Físicos"
