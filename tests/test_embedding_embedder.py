"""
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.embedding.embedder import Embedder
from src.core.embedding_config import EmbeddingConfig


@patch('src.embedding.embedder.TextEncoder')
class TestEmbedder:
    """
    """

    def test_embedder_initialization(self, mock_encoder):
        """
        """
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.embedding_dim = 768
        mock_encoder.return_value = mock_encoder_instance
        
        config = EmbeddingConfig()
        embedder = Embedder(config)
        
        assert embedder.config == config

    def test_embedder_run_empty_chunks(self, mock_encoder):
        """
        """
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.embedding_dim = 768
        mock_encoder.return_value = mock_encoder_instance
        
        config = EmbeddingConfig()
        embedder = Embedder(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            chunks_file = Path(tmpdir) / "chunks.jsonl"
            chunks_file.write_text("")
            
            config.paths.chunks_dir = Path(tmpdir)
            embedder.config = config
            
            output = embedder.run()
            assert output is not None

    @patch('src.embedding.embedder.Embedder._load_chunks')
    @patch('src.embedding.embedder.Embedder._save')
    def test_embedder_build_embedding_text(self, mock_save, mock_load, mock_encoder):
        """
        """
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.embedding_dim = 768
        mock_encoder.return_value = mock_encoder_instance
        
        config = EmbeddingConfig()
        embedder = Embedder(config)
        
        chunk = {
            "content": "test content",
            "caption": None
        }
        
        result = embedder._build_embedding_text(chunk)
        assert isinstance(result, str)

    @patch('src.embedding.embedder.Embedder._load_chunks')
    @patch('src.embedding.embedder.Embedder._save')
    def test_embedder_build_embedding_text_with_caption(self, mock_save, mock_load, mock_encoder):
        """
        """
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.embedding_dim = 768
        mock_encoder.return_value = mock_encoder_instance
        
        config = EmbeddingConfig()
        embedder = Embedder(config)
        
        chunk = {
            "content": "table content",
            "caption": "Table 1: Results"
        }
        
        result = embedder._build_embedding_text(chunk)
        assert isinstance(result, str)
        if chunk["caption"]:
            assert "Table 1" in result or "table content" in result
