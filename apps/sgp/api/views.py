"""Views do app sgp."""

from typing import Any

from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sgp import service
from apps.sgp.api.serializers import MetricasSgpSerializer


def _param_int(request: Request, nome: str) -> int:
    """Lê um parâmetro de query obrigatório e inteiro.

    Raises:
        ValidationError: Quando o parâmetro está ausente ou não é inteiro.
    """
    valor = request.query_params.get(nome)
    if not valor:
        raise ValidationError({nome: ["Parâmetro obrigatório."]})
    try:
        return int(valor)
    except (TypeError, ValueError) as erro:
        raise ValidationError(
            {nome: ["Deve ser um número inteiro."]}
        ) from erro


class MetricasSgpView(APIView):
    """Métricas do SGP para o painel da COPED, via leitura do banco."""

    serializer_class = MetricasSgpSerializer

    @extend_schema(
        tags=["sgp"],
        summary="Métricas do SGP (COPED)",
        operation_id="sgp_coped_metricas",
        parameters=[
            OpenApiParameter(
                "ano_letivo", int, required=True, description="Ano letivo."
            ),
            OpenApiParameter(
                "bimestre", int, required=True, description="Bimestre."
            ),
        ],
        responses=MetricasSgpSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas do SGP para o período."""
        ano_letivo = _param_int(request, "ano_letivo")
        bimestre = _param_int(request, "bimestre")
        serializer = self.serializer_class(
            data=service.obter_metricas(ano_letivo, bimestre)
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
