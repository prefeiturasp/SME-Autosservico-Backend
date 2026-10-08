"""Configuração do app intranet."""

from django.apps import AppConfig


class IntranetConfig(AppConfig):
    """Gateway de leitura do banco do Intranet para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.intranet"
    verbose_name = "Intranet"
