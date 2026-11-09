"""Rotas do app sgp."""

from django.urls import path

from apps.sgp.api.views import MetricasSgpView
from apps.sgp.api.views import PeriodosSgpView

app_name = "sgp"
urlpatterns = [
    path(
        "sgp/coped/metricas/",
        MetricasSgpView.as_view(),
        name="metricas",
    ),
    path(
        "sgp/coped/periodos/",
        PeriodosSgpView.as_view(),
        name="periodos",
    ),
]
