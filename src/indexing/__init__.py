"""
Módulo de indexação vetorial do pipeline RAG.
"""

from .indexer import Indexer
from src.core.indexing_config import IndexingConfig

__all__ = [
    "Indexer",
    "IndexingConfig",
]
