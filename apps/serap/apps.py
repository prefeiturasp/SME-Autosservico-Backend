"""Configuração do app serap."""

from django.apps import AppConfig


class SerapConfig(AppConfig):
    """Gateway de leitura do banco do SERAp Estudantes para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.serap"
    verbose_name = "SERAp"
