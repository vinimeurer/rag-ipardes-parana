"""
Módulo core do projeto RAG IPARDES Paraná.

Centraliza todas as configurações e utilitários do projeto.
"""

# Import configuration modules
from .directory_config import (
    PROJECT_ROOT,
    DATA_DIR,
    MODELS_DIR,
    OUTPUTS_DIR,
    LOGS_DIR,
    SCRIPTS_DIR,
    RAW_DATA_DIR,
    EXTRACTED_DATA_DIR,
    PROCESSED_DATA_DIR,
    CHUNKS_DATA_DIR,
    EMBEDDINGS_DATA_DIR,
    VECTOR_DB_DIR,
    EMBEDDINGS_MODELS_DIR,
    PROMPTS_OUTPUT_DIR,
    RETRIEVAL_LOGS_DIR,
    RESPONSES_OUTPUT_DIR,
    EVALUATIONS_OUTPUT_DIR,
    create_directories,
)

from .pdf_config import (
    PDF_SOURCES,
    PDFSourceConfig,
    ContentFilterConfig,
)

from .chunking_config import (
    ChunkingConfig,
    ChunkingPaths,
)

from .embedding_config import (
    EmbeddingConfig,
    EmbeddingPaths,
)

from .indexing_config import (
    IndexingConfig,
    IndexingPaths,
)

from .ingestion_config import (
    IngestionPipelineConfig,
    ExtractionOutputConfig,
    DoclingBackendConfig,
)

from .preprocessing_config import (
    PreprocessingConfig,
    PreprocessingPaths,
    CleaningConfig,
    TableProcessingConfig,
)

from .logging_config import (
    LOG_LEVEL,
    LOG_FORMAT,
)

from .logger import setup_logger

__all__ = [
    # Directory Configuration
    "PROJECT_ROOT",
    "DATA_DIR",
    "MODELS_DIR",
    "OUTPUTS_DIR",
    "LOGS_DIR",
    "SCRIPTS_DIR",
    "RAW_DATA_DIR",
    "EXTRACTED_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "CHUNKS_DATA_DIR",
    "EMBEDDINGS_DATA_DIR",
    "VECTOR_DB_DIR",
    "EMBEDDINGS_MODELS_DIR",
    "PROMPTS_OUTPUT_DIR",
    "RETRIEVAL_LOGS_DIR",
    "RESPONSES_OUTPUT_DIR",
    "EVALUATIONS_OUTPUT_DIR",
    "create_directories",
    # PDF Configuration
    "PDF_SOURCES",
    "PDFSourceConfig",
    "ContentFilterConfig",
    # Chunking Configuration
    "ChunkingConfig",
    "ChunkingPaths",
    # Embedding Configuration
    "EmbeddingConfig",
    "EmbeddingPaths",
    # Indexing Configuration
    "IndexingConfig",
    "IndexingPaths",
    # Ingestion Configuration
    "IngestionPipelineConfig",
    "ExtractionOutputConfig",
    "DoclingBackendConfig",
    # Preprocessing Configuration
    "PreprocessingConfig",
    "PreprocessingPaths",
    "CleaningConfig",
    "TableProcessingConfig",
    # Logging Configuration
    "LOG_LEVEL",
    "LOG_FORMAT",
    "setup_logger",]
