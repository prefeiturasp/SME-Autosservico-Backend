"""Views do app sgp."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sgp import service
from apps.sgp.api.serializers import MetricasSgpSerializer
from apps.sgp.api.serializers import PeriodosSgpSerializer
from apps.sgp.api.serializers import SgpFiltrosQuerySerializer


class MetricasSgpView(APIView):
    """Métricas do SGP para o painel da COPED, via leitura do banco."""

    serializer_class = MetricasSgpSerializer

    @extend_schema(
        tags=["sgp"],
        summary="Métricas do SGP (COPED)",
        operation_id="sgp_coped_metricas",
        parameters=[SgpFiltrosQuerySerializer],
        responses=MetricasSgpSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do SGP para o período."""
        filtros = SgpFiltrosQuerySerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        serializer = self.serializer_class(
            data=service.obter_metricas(filtros.como_periodo())
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class PeriodosSgpView(APIView):
    """Opções do filtro de período do SGP."""

    serializer_class = PeriodosSgpSerializer

    @extend_schema(
        tags=["sgp"],
        summary="Períodos do filtro de métricas do SGP (COPED)",
        operation_id="sgp_coped_periodos",
        responses=PeriodosSgpSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna os bimestres já iniciados."""
        serializer = self.serializer_class(data=service.obter_periodos())
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
