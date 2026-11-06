"""Filtro de período do SGP.

A EJA é semestral, com 2 bimestres por semestre. Fundamental/Médio é anual.
"""

from dataclasses import dataclass
from typing import Any

SEGMENTO_FUNDAMENTAL_MEDIO = "fundamental_medio"
SEGMENTO_EJA = "eja"
SEGMENTOS = (SEGMENTO_FUNDAMENTAL_MEDIO, SEGMENTO_EJA)

BIMESTRES_POR_SEGMENTO = {
    SEGMENTO_FUNDAMENTAL_MEDIO: 4,
    SEGMENTO_EJA: 2,
}


@dataclass(frozen=True)
class Periodo:
    """Período consultado nas métricas do SGP."""

    ano_letivo: int
    bimestre: int
    segmento: str = SEGMENTO_FUNDAMENTAL_MEDIO
    semestre: int | None = None

    def parametros(self) -> dict[str, Any]:
        """Parâmetros nomeados das consultas filtradas por segmento."""
        return {
            "ano_letivo": self.ano_letivo,
            "bimestre": self.bimestre,
            "segmento": self.segmento,
            "semestre": self.semestre,
        }

    def como_contrato(self) -> dict[str, Any]:
        """Bloco ``periodo`` do contrato."""
        return {
            "ano_letivo": self.ano_letivo,
            "segmento": self.segmento,
            "semestre": self.semestre,
            "bimestre": self.bimestre,
        }
