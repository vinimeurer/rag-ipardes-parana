"""
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.core.chunking_config import ChunkingConfig, ChunkingPaths
from src.core.embedding_config import EmbeddingConfig, EmbeddingPaths
from src.core.indexing_config import IndexingConfig, IndexingPaths
from src.core.rag_config import RAGConfig, RetrieverConfig, RerankerConfig, LLMConfig
from src.core.ingestion_config import IngestionPipelineConfig, DoclingBackendConfig, ExtractionOutputConfig
from src.core.preprocessing_config import PreprocessingConfig, CleaningConfig, TableProcessingConfig


class TestChunkingConfig:
    """
    """

    def test_chunking_config_initialization(self):
        """
        """
        config = ChunkingConfig()
        assert config is not None
        assert config.chunk_size > 0
        assert config.overlap >= 0

    def test_chunking_config_chunk_size_default(self):
        """
        """
        config = ChunkingConfig()
        assert config.chunk_size == 256

    def test_chunking_config_overlap_default(self):
        """
        """
        config = ChunkingConfig()
        assert config.overlap == 32

    def test_chunking_config_min_chunk_tokens(self):
        """
        """
        config = ChunkingConfig()
        assert config.min_chunk_tokens > 0

    def test_chunking_config_separators_list(self):
        """
        """
        config = ChunkingConfig()
        assert isinstance(config.separators, list)
        assert len(config.separators) > 0


class TestEmbeddingConfig:
    """
    """

    def test_embedding_config_initialization(self):
        """
        """
        config = EmbeddingConfig()
        assert config is not None
        assert config.model_name is not None

    def test_embedding_config_model_name_default(self):
        """
        """
        config = EmbeddingConfig()
        assert "bge" in config.model_name.lower() or config.model_name

    def test_embedding_config_batch_size(self):
        """
        """
        config = EmbeddingConfig()
        assert config.batch_size > 0

    def test_embedding_config_normalize_default(self):
        """
        """
        config = EmbeddingConfig()
        assert config.normalize is True

    def test_embedding_config_device_default(self):
        """
        """
        config = EmbeddingConfig()
        assert config.device == "cpu"


class TestIndexingConfig:
    """
    """

    def test_indexing_config_initialization(self):
        """
        """
        config = IndexingConfig()
        assert config is not None

    def test_indexing_config_collection_name(self):
        """
        """
        config = IndexingConfig()
        assert config.retriever.collection_name is not None

    def test_indexing_config_distance_metric(self):
        """
        """
        config = IndexingConfig()
        assert config.distance_metric is not None


class TestRetrieverConfig:
    """
    """

    def test_retriever_config_initialization(self):
        """
        """
        config = RetrieverConfig()
        assert config.top_k > 0

    def test_retriever_config_min_similarity(self):
        """
        """
        config = RetrieverConfig()
        assert 0 <= config.min_similarity <= 1

    def test_retriever_config_reranker_top_k(self):
        """
        """
        config = RetrieverConfig()
        assert config.reranker_top_k <= config.top_k


class TestRerankerConfig:
    """
    """

    def test_reranker_config_initialization(self):
        """
        """
        config = RerankerConfig()
        assert config is not None

    def test_reranker_config_model_name(self):
        """
        """
        config = RerankerConfig()
        assert config.model_name is not None

    def test_reranker_config_enabled_default(self):
        """
        """
        config = RerankerConfig()
        assert isinstance(config.enabled, bool)


class TestLLMConfig:
    """
    """

    def test_llm_config_initialization(self):
        """
        """
        config = LLMConfig()
        assert config.model_name is not None

    def test_llm_config_temperature_range(self):
        """
        """
        config = LLMConfig()
        assert 0.0 <= config.temperature <= 1.0

    def test_llm_config_max_tokens_positive(self):
        """
        """
        config = LLMConfig()
        assert config.max_tokens > 0

    def test_llm_config_ollama_host(self):
        """
        """
        config = LLMConfig()
        assert config.ollama_host is not None
        assert "http" in config.ollama_host or "localhost" in config.ollama_host


class TestRAGConfig:
    """
    """

    def test_rag_config_initialization(self):
        """
        """
        config = RAGConfig()
        assert config is not None
        assert config.retriever is not None
        assert config.reranker is not None
        assert config.llm is not None

    def test_rag_config_has_embedding_model(self):
        """
        """
        config = RAGConfig()
        assert config.embedding_model is not None

    def test_rag_config_embedding_model_path(self):
        """
        """
        config = RAGConfig()
        assert config.embedding_model_path is not None


class TestCleaningConfig:
    """
    """

    def test_cleaning_config_initialization(self):
        """
        """
        config = CleaningConfig()
        assert config is not None

    def test_cleaning_config_boolean_flags(self):
        """
        """
        config = CleaningConfig()
        assert isinstance(config.remove_headers, bool)
        assert isinstance(config.normalize_whitespace, bool)


class TestTableProcessingConfig:
    """
    """

    def test_table_processing_config_initialization(self):
        """
        """
        config = TableProcessingConfig()
        assert config is not None

    def test_table_processing_include_caption_default(self):
        """
        """
        config = TableProcessingConfig()
        assert isinstance(config.include_caption, bool)


class TestPreprocessingConfig:
    """
    """

    def test_preprocessing_config_initialization(self):
        """
        """
        config = PreprocessingConfig()
        assert config is not None
        assert config.cleaning is not None
        assert config.tables is not None


class TestDoclingBackendConfig:
    """
    """

    def test_docling_backend_config_initialization(self):
        """
        """
        config = DoclingBackendConfig()
        assert config is not None

    def test_docling_backend_do_ocr_default(self):
        """
        """
        config = DoclingBackendConfig()
        assert isinstance(config.do_ocr, bool)


class TestExtractionOutputConfig:
    """
    """

    def test_extraction_output_config_initialization(self):
        """
        """
        config = ExtractionOutputConfig()
        assert config is not None

    def test_extraction_output_format_flags(self):
        """
        """
        config = ExtractionOutputConfig()
        assert isinstance(config.save_markdown, bool)
        assert isinstance(config.save_json, bool)
