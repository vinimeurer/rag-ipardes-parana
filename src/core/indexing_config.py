"""
Configurações centralizadas para o pipeline de indexação vetorial.
"""

from dataclasses import dataclass, field
from pathlib import Path


EMBEDDINGS_DATA_DIR = Path("data/embeddings")
VECTOR_DB_DIR = Path("data/vector_db")


@dataclass
class IndexingPaths:
    """Caminhos de entrada e saída do pipeline de indexação."""

    embeddings_dir: Path = EMBEDDINGS_DATA_DIR
    vector_db_dir: Path = VECTOR_DB_DIR


@dataclass
class IndexingConfig:
    """Parâmetros de configuração para indexação vetorial.

    Attributes:
        paths: Caminhos de entrada e saída.
        collection_name: Nome da coleção no ChromaDB.
        embeddings_filename: Nome do arquivo JSONL de entrada com embeddings.
        distance_metric: Métrica de distância usada pelo ChromaDB.
            'cosine' é adequado para vetores normalizados.
        batch_size: Número de chunks inseridos por lote no ChromaDB.
    """

    paths: IndexingPaths = field(default_factory=IndexingPaths)
    collection_name: str = "chunks"
    embeddings_filename: str = "chunks_with_embeddings.jsonl"
    distance_metric: str = "cosine"
    batch_size: int = 100
