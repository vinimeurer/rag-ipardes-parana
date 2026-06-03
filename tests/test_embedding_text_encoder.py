"""
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from src.embedding.text_encoder import TextEncoder


@patch('src.embedding.text_encoder.SentenceTransformer')
class TestTextEncoder:
    """
    """

    def test_text_encoder_initialization_with_cached_model(self, mock_transformer):

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model"
            model_path.mkdir()
            
            mock_instance = MagicMock()
            mock_instance.get_sentence_embedding_dimension.return_value = 768
            mock_transformer.return_value = mock_instance
            
            encoder = TextEncoder(
                model_name="test_model",
                model_local_path=model_path,
                models_dir=Path(tmpdir),
                device="cpu",
                normalize=True
            )
            
            assert encoder.model_name == "test_model"
            assert encoder.normalize is True
            assert encoder.embedding_dim == 768

    def test_text_encoder_initialization_without_cached_model(self, mock_transformer):

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent_model"
            
            mock_instance = MagicMock()
            mock_instance.get_sentence_embedding_dimension.return_value = 768
            mock_transformer.return_value = mock_instance
            
            encoder = TextEncoder(
                model_name="test_model",
                model_local_path=model_path,
                models_dir=Path(tmpdir),
                device="cpu"
            )
            
            assert encoder.embedding_dim == 768

    def test_text_encoder_encode_single_text(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_instance.encode.return_value = [[0.1] * 768]
        mock_transformer.return_value = mock_instance
        
        encoder = TextEncoder(
            model_name="test",
            model_local_path=Path("/fake"),
            models_dir=Path("/fake")
        )
        
        result = encoder.encode_single("test text")
        
        assert isinstance(result, list)
        assert len(result) == 768

    def test_text_encoder_encode_multiple_texts(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_instance.encode.return_value = [[0.1] * 768, [0.2] * 768]
        mock_transformer.return_value = mock_instance
        
        encoder = TextEncoder(
            model_name="test",
            model_local_path=Path("/fake"),
            models_dir=Path("/fake")
        )
        
        result = encoder.encode(["text1", "text2"])
        
        assert isinstance(result, list)
        assert len(result) == 2

    def test_text_encoder_encode_batch_size(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_instance.encode.return_value = [[0.1] * 768]
        mock_transformer.return_value = mock_instance
        
        encoder = TextEncoder(
            model_name="test",
            model_local_path=Path("/fake"),
            models_dir=Path("/fake")
        )
        
        encoder.encode(["text"], batch_size=32)
        
        call_args = mock_instance.encode.call_args
        assert call_args[1]["batch_size"] == 32

    def test_text_encoder_normalize_embeddings(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_instance.encode.return_value = [[0.1] * 768]
        mock_transformer.return_value = mock_instance
        
        encoder = TextEncoder(
            model_name="test",
            model_local_path=Path("/fake"),
            models_dir=Path("/fake"),
            normalize=True
        )
        
        encoder.encode(["text"])
        
        call_args = mock_instance.encode.call_args
        assert call_args[1]["normalize_embeddings"] is True

    def test_text_encoder_device_cpu(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_transformer.return_value = mock_instance
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model"
            model_path.mkdir()
            
            TextEncoder(
                model_name="test",
                model_local_path=model_path,
                models_dir=Path(tmpdir),
                device="cpu"
            )
            
            assert mock_transformer.called

    def test_text_encoder_embedding_dimension(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 1024
        mock_transformer.return_value = mock_instance
        
        encoder = TextEncoder(
            model_name="test",
            model_local_path=Path("/fake"),
            models_dir=Path("/fake")
        )
        
        assert encoder.embedding_dim == 1024

    def test_text_encoder_empty_text_list(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_instance.encode.return_value = []
        mock_transformer.return_value = mock_instance
        
        encoder = TextEncoder(
            model_name="test",
            model_local_path=Path("/fake"),
            models_dir=Path("/fake")
        )
        
        result = encoder.encode([])
        
        assert isinstance(result, list)

    def test_text_encoder_model_name_stored(self, mock_transformer):

        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_transformer.return_value = mock_instance
        
        model_name = "bert-large-portuguese"
        encoder = TextEncoder(
            model_name=model_name,
            model_local_path=Path("/fake"),
            models_dir=Path("/fake")
        )
        
        assert encoder.model_name == model_name
