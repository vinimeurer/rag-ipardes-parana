"""
Configurações centralizadas para o pipeline de chunking.

Define as classes de configuração usando dataclasses para organizar os parâmetros
relacionados à geração de chunks para o pipeline RAG.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .directory_config import PROCESSED_DATA_DIR, CHUNKS_DATA_DIR


@dataclass
class ChunkingPaths:
    """Caminhos de entrada e saída do pipeline de chunking."""

    processed_dir: Path = PROCESSED_DATA_DIR
    chunks_dir: Path = CHUNKS_DATA_DIR


@dataclass
class ChunkingConfig:
    """Parâmetros de configuração para geração de chunks.

    Attributes:
        paths: Caminhos de entrada e saída.
        chunk_size: Número máximo de tokens por chunk de texto.
        overlap: Número de tokens de sobreposição entre chunks consecutivos.
        min_chunk_tokens: Chunks com menos tokens que este valor são descartados.
        max_table_tokens: Tabelas com mais tokens que este valor são truncadas com aviso.
        separators: Separadores usados no recursive splitting, em ordem de preferência.
    """

    paths: ChunkingPaths = field(default_factory=ChunkingPaths)
    chunk_size: int = 256
    overlap: int = 32
    min_chunk_tokens: int = 10
    max_table_tokens: int = 512
    separators: list[str] = field(default_factory=lambda: ["\n\n", "\n", " "])
