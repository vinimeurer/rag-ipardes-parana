"""
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_directory():
    """
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_logger():
    """
    """
    logger = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


@pytest.fixture
def mock_config():
    """
    """
    config = MagicMock()
    config.chunk_size = 256
    config.overlap = 32
    config.batch_size = 64
    return config


@pytest.fixture
def sample_chunk():
    """
    """
    from src.chunking.chunk_dataclass import Chunk
    return Chunk(
        chunk_id="test_001_00",
        document="test_doc",
        page=1,
        sections=["Introduction"],
        type="text",
        content="This is test content for chunking",
        token_count=6,
        is_auxiliary=False,
        caption=None
    )


@pytest.fixture
def sample_chunks(sample_chunk):
    """
    """
    chunks = []
    for i in range(5):
        chunk = sample_chunk
        chunk.chunk_id = f"test_{i:03d}_00"
        chunks.append(chunk)
    return chunks


@pytest.fixture
def sample_retrieved_chunk():
    """
    """
    from src.rag.retriever import RetrievedChunk
    return RetrievedChunk(
        chunk_id="test_001",
        document="desenvolvimento_paranaense",
        page=1,
        sections=["Introduction"],
        type="text",
        content="Sample retrieved content",
        caption=None,
        similarity=0.95
    )


@pytest.fixture
def sample_retrieved_chunks(sample_retrieved_chunk):
    """
    """
    chunks = []
    for i in range(3):
        chunk = sample_retrieved_chunk
        chunk.chunk_id = f"chunk_{i}"
        chunk.similarity = 0.9 - (i * 0.1)
        chunks.append(chunk)
    return chunks


@pytest.fixture
def sample_cleaning_config():
    """
    """
    from src.core.preprocessing_config import CleaningConfig
    return CleaningConfig(
        remove_headers=True,
        remove_page_numbers=True,
        remove_hyphenation=True,
        normalize_whitespace=True,
        dedup_empty_lines=True
    )


@pytest.fixture
def sample_chunking_config():
    """
    """
    from src.core.chunking_config import ChunkingConfig
    return ChunkingConfig(
        chunk_size=256,
        overlap=32,
        min_chunk_tokens=10,
        max_table_tokens=512
    )


@pytest.fixture
def sample_embedding_config():
    """
    """
    from src.core.embedding_config import EmbeddingConfig
    return EmbeddingConfig(
        batch_size=64,
        normalize=True,
        device="cpu"
    )


@pytest.fixture
def sample_rag_config():
    """
    """
    from src.core.rag_config import RAGConfig
    return RAGConfig()


@pytest.fixture
def mock_text_cleaner(sample_cleaning_config):
    """
    """
    from src.preprocessing.text_cleaner import TextCleaner
    return TextCleaner(sample_cleaning_config)


@pytest.fixture
def mock_chunker(sample_chunking_config):
    """
    """
    from src.chunking.chunker import Chunker
    return Chunker(sample_chunking_config)
