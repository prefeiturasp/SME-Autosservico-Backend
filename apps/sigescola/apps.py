"""Configuração do app sigescola."""

from django.apps import AppConfig


class SigescolaConfig(AppConfig):
    """Gateway de leitura do banco do SIG-Escola (PTRF) para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sigescola"
    verbose_name = "SIG-Escola"
