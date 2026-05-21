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
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH,
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

from .retrieval_config import (
    RETRIEVAL_TOP_K,
    SIMILARITY_THRESHOLD,
    USE_RERANKING,
    USE_MMR,
    CACHE_EMBEDDINGS,
    CACHE_VECTOR_STORE,
)

from .llm_config import (
    LLM_MODEL_NAME,
    LLM_CONTEXT_WINDOW,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TOP_P,
    OLLAMA_API_URL,
    LLAMA_CPP_LIBRARY_PATH,
)

from .api_config import (
    API_HOST,
    API_PORT,
    API_DEBUG,
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
    "FAISS_INDEX_PATH",
    "FAISS_METADATA_PATH",
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
    "setup_logger",
    # Retrieval Configuration
    "RETRIEVAL_TOP_K",
    "SIMILARITY_THRESHOLD",
    "USE_RERANKING",
    "USE_MMR",
    "CACHE_EMBEDDINGS",
    "CACHE_VECTOR_STORE",
    # LLM Configuration
    "LLM_MODEL_NAME",
    "LLM_CONTEXT_WINDOW",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "LLM_TOP_P",
    "OLLAMA_API_URL",
    "LLAMA_CPP_LIBRARY_PATH",
    # API Configuration
    "API_HOST",
    "API_PORT",
    "API_DEBUG",
]
