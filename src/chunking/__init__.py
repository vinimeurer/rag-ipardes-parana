"""
Módulo de chunking do pipeline RAG.
"""

from .chunk_dataclass import Chunk
from .chunker import Chunker
from .text_splitter import RecursiveTextSplitter, count_tokens
from ..core.chunking_config import ChunkingConfig

__all__ = [
    "Chunk",
    "Chunker",
    "ChunkingConfig",
    "RecursiveTextSplitter",
    "count_tokens",
]
