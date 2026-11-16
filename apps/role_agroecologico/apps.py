"""Configuração do app role_agroecologico."""

from django.apps import AppConfig


class RoleAgroecologicoConfig(AppConfig):
    """Gateway de leitura do banco do Rolê Agroecológico para métricas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.role_agroecologico"
    verbose_name = "Rolê Agroecológico"
