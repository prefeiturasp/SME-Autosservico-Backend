"""Rotas do app serap."""

from django.urls import path

from apps.serap.api.views import MetricasProvasSerapView

app_name = "serap"
urlpatterns = [
    path(
        "serap/provas/metricas/",
        MetricasProvasSerapView.as_view(),
        name="provas-metricas",
    ),
]
