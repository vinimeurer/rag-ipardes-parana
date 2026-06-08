"""
"""

import pytest
from unittest.mock import patch, MagicMock, Mock

from src.rag.llm_client import LLMClient
from src.core.rag_config import LLMConfig


class TestLLMClient:
    """
    """

    def test_llm_client_initialization(self):

        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        
        client = LLMClient(config)
        
        assert client.config == config
        assert client.logger is not None

    def test_llm_client_config_values(self):

        config = LLMConfig(
            model_name="llama2",
            temperature=0.5,
            max_tokens=2048,
            ollama_host="http://custom:11434"
        )
        
        client = LLMClient(config)
        
        assert client.config.model_name == "llama2"
        assert client.config.temperature == 0.5
        assert client.config.max_tokens == 2048

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_basic(self, mock_generate):

        mock_generate.return_value = {"response": "Test response"}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.generate("Test prompt")
        
        assert result == "Test response"
        mock_generate.assert_called_once()

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_with_whitespace_trimmed(self, mock_generate):

        mock_generate.return_value = {"response": "  Response with spaces  "}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.generate("Test prompt")
        
        assert result == "Response with spaces"

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_passes_temperature(self, mock_generate):

        mock_generate.return_value = {"response": "Response"}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.7,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        client.generate("Test prompt")
        
        call_args = mock_generate.call_args
        assert call_args[1]["options"]["temperature"] == 0.7

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_passes_max_tokens(self, mock_generate):

        mock_generate.return_value = {"response": "Response"}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=512,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        client.generate("Test prompt")
        
        call_args = mock_generate.call_args
        assert call_args[1]["options"]["num_predict"] == 512

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_exception_raises_runtime_error(self, mock_generate):

        mock_generate.side_effect = Exception("Ollama not running")
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        with pytest.raises(RuntimeError):
            client.generate("Test prompt")

    @patch('src.rag.llm_client.ollama.list')
    def test_is_available_true(self, mock_list):

        mock_model = Mock()
        mock_model.model = "llama2:latest"
        mock_list.return_value = Mock(models=[mock_model])
        
        config = LLMConfig(
            model_name="llama2",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.is_available()
        
        assert result is True

    @patch('src.rag.llm_client.ollama.list')
    def test_is_available_false(self, mock_list):

        mock_model = Mock()
        mock_model.model = "other_model:latest"
        mock_list.return_value = Mock(models=[mock_model])
        
        config = LLMConfig(
            model_name="llama2",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.is_available()
        
        assert result is False

    @patch('src.rag.llm_client.ollama.list')
    def test_is_available_exception_returns_false(self, mock_list):

        mock_list.side_effect = Exception("Connection error")
        
        config = LLMConfig(
            model_name="llama2",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.is_available()
        
        assert result is False

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_long_prompt(self, mock_generate):

        mock_generate.return_value = {"response": "Response"}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        long_prompt = "word " * 10000
        result = client.generate(long_prompt)
        
        assert result == "Response"

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_empty_prompt(self, mock_generate):

        mock_generate.return_value = {"response": "Response"}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.generate("")
        
        assert result == "Response"

    @patch('src.rag.llm_client.ollama.generate')
    def test_generate_unicode_text(self, mock_generate):

        mock_generate.return_value = {"response": "Resposta com acentuação"}
        
        config = LLMConfig(
            model_name="test_model",
            temperature=0.1,
            max_tokens=1024,
            ollama_host="http://localhost:11434"
        )
        client = LLMClient(config)
        
        result = client.generate("Pergunta com acentuação")
        
        assert "acentuação" in result
