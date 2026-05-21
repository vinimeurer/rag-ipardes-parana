"""
Configurações centralizadas para o pipeline de embedding.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .directory_config import CHUNKS_DATA_DIR, EMBEDDINGS_DATA_DIR, EMBEDDINGS_MODELS_DIR


@dataclass
class EmbeddingPaths:
    """Caminhos de entrada, saída e cache de modelos do pipeline de embedding."""

    chunks_dir: Path = CHUNKS_DATA_DIR
    embeddings_dir: Path = EMBEDDINGS_DATA_DIR
    models_dir: Path = EMBEDDINGS_MODELS_DIR


@dataclass
class EmbeddingConfig:
    """Parâmetros de configuração para geração de embeddings.

    Attributes:
        paths: Caminhos de entrada, saída e cache de modelos.
        model_name: Nome do modelo sentence-transformers.
        batch_size: Número de chunks processados por vez pelo modelo.
        normalize: Se True, normaliza os vetores para norma unitária.
        device: Dispositivo de inferência ('cpu' ou 'cuda').
        chunks_filename: Nome do arquivo JSONL de entrada.
        output_filename: Nome do arquivo JSONL de saída com embeddings.
    """

    paths: EmbeddingPaths = field(default_factory=EmbeddingPaths)
    model_name: str = "BAAI/bge-m3" # "paraphrase-multilingual-mpnet-base-v2"
    batch_size: int = 64
    normalize: bool = True
    device: str = "cpu"
    chunks_filename: str = "chunks.jsonl"
    output_filename: str = "chunks_with_embeddings.jsonl"

    @property
    def model_local_path(self) -> Path:
        """Caminho local esperado para o modelo após download.

        Returns:
            Path completo para a pasta do modelo em models/embeddings/.
        """
        return self.paths.models_dir / self.model_name
