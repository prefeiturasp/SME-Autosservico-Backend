"""Testes do router central de ViewSets do projeto."""

from config.api_router import app_name
from config.api_router import router


class TestApiRouter:
    """Testes cobrindo o router central em config/api_router.py."""

    def test_app_name(self) -> None:
        """O app_name do router é 'api'."""
        assert app_name == "api"

    def test_router_sem_viewsets_registrados(self) -> None:
        """Nenhum ViewSet foi registrado ainda no router central."""
        assert router.registry == []
