"""Rotas do app role_agroecologico."""

from django.urls import path

from apps.role_agroecologico.api.views import MetricasRoleAgroecologicoView

app_name = "role_agroecologico"
urlpatterns = [
    path(
        "role-agroecologico/metricas/",
        MetricasRoleAgroecologicoView.as_view(),
        name="metricas",
    ),
]
