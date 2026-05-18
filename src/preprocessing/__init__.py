"""
Módulo de preprocessamento para o pipeline RAG IPARDES.

Exporta as classes principais para uso externo.
"""

from .preprocessor import Preprocessor
from .preprocessor_utils import ProcessResult

__all__ = [
    "Preprocessor",
    "ProcessResult",
]
