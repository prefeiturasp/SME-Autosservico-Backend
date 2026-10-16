"""Views do app serap."""

from typing import Any

from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.serap import service
from apps.serap.api.serializers import MetricasProvasSerapSerializer


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


class MetricasProvasSerapView(APIView):
    """Métricas de provas do SERAp, via leitura direta do banco."""

    serializer_class = MetricasProvasSerapSerializer

    @extend_schema(
        tags=["serap"],
        summary="Métricas de provas do SERAp",
        operation_id="serap_provas_metricas",
        parameters=[
            OpenApiParameter("ano", int, required=True, description="Ano."),
            OpenApiParameter(
                "bimestre", int, required=True, description="Bimestre."
            ),
        ],
        responses=MetricasProvasSerapSerializer,
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna o contrato de métricas de provas do SERAp."""
        ano = _param_int(request, "ano")
        bimestre = _param_int(request, "bimestre")
        serializer = self.serializer_class(
            data=service.obter_provas(ano, bimestre)
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
