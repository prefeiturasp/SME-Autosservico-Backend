"""Views do app intranet."""

import re
from typing import Any

from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intranet import service
from apps.intranet.api.serializers import MetricasIntranetSerializer

_FORMATO_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _param_periodo(request: Request) -> str:
    """Lê o parâmetro opcional ``periodo`` (padrão ``geral``).

    Raises:
        ValidationError: Quando o valor não é um dos períodos aceitos.
    """
    periodo = request.query_params.get("periodo") or service.PERIODO_GERAL
    if periodo not in service.PERIODOS:
        opcoes = ", ".join(service.PERIODOS)
        raise ValidationError({"periodo": [f"Use um de: {opcoes}."]})
    return periodo


def _param_mes(request: Request) -> str | None:
    """Lê o parâmetro opcional ``mes`` no formato ``AAAA-MM``.

    Raises:
        ValidationError: Quando o valor não está no formato ``AAAA-MM``.
    """
    mes = request.query_params.get("mes") or None
    if mes is not None and not _FORMATO_MES.match(mes):
        raise ValidationError({"mes": ["Use o formato AAAA-MM."]})
    return mes


class MetricasIntranetView(APIView):
    """Métricas do Intranet, via leitura direta do banco."""

    serializer_class = MetricasIntranetSerializer

    @extend_schema(
        tags=["intranet"],
        summary="Métricas do Intranet",
        operation_id="intranet_metricas",
        parameters=[
            OpenApiParameter(
                "periodo",
                str,
                required=False,
                enum=list(service.PERIODOS),
                description=(
                    "Recorte dos cards por tipo/ganhador/DRE (janela "
                    "móvel). Padrão: geral (sem filtro de data)."
                ),
            ),
            OpenApiParameter(
                "mes",
                str,
                required=False,
                description=(
                    "Mês (AAAA-MM) do card por DRE de Ordem de Inscrição. "
                    "Ausente: sem filtro de data."
                ),
            ),
        ],
        responses=MetricasIntranetSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do Intranet."""
        periodo = _param_periodo(request)
        mes = _param_mes(request)
        serializer = self.serializer_class(
            data=service.obter_metricas(periodo, mes)
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
