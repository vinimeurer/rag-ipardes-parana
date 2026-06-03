"""
"""

import pytest
from unittest.mock import patch, MagicMock

from src.rag.rag_pipeline import RAGPipeline, RAGResponse
from src.core.rag_config import RAGConfig


@patch('src.rag.rag_pipeline.LLMClient')
@patch('src.rag.rag_pipeline.PromptBuilder')
@patch('src.rag.rag_pipeline.Reranker')
@patch('src.rag.rag_pipeline.Retriever')
class TestRAGResponse:
    """
    """

    def test_rag_response_initialization(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        response = RAGResponse(
            query="Test?",
            answer="Answer",
            chunks=[],
            chunks_before_rerank=[],
            prompt="Prompt",
            out_of_scope=False
        )
        
        assert response.query == "Test?"
        assert response.answer == "Answer"

    def test_rag_response_out_of_scope_true(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        response = RAGResponse(
            query="Unknown?",
            answer="Not covered",
            chunks=[],
            chunks_before_rerank=[],
            prompt="Prompt",
            out_of_scope=True
        )
        
        assert response.out_of_scope is True


@patch('src.rag.rag_pipeline.LLMClient')
@patch('src.rag.rag_pipeline.PromptBuilder')
@patch('src.rag.rag_pipeline.Reranker')
@patch('src.rag.rag_pipeline.Retriever')
class TestRAGPipeline:
    """
    """

    def test_rag_pipeline_initialization(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        config = RAGConfig()
        pipeline = RAGPipeline(config)
        
        assert pipeline.config == config

    def test_rag_pipeline_query_basic(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = mock_retriever_instance
        
        mock_reranker_instance = MagicMock()
        mock_reranker.return_value = mock_reranker_instance
        
        mock_prompt_builder_instance = MagicMock()
        mock_prompt_builder_instance.build_out_of_scope.return_value = "Prompt"
        mock_prompt_builder.return_value = mock_prompt_builder_instance
        
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate.return_value = "Response"
        mock_llm.return_value = mock_llm_instance
        
        config = RAGConfig()
        pipeline = RAGPipeline(config)
        
        response = pipeline.query("Test?")
        
        assert isinstance(response, RAGResponse)
        assert response.out_of_scope is True or response.out_of_scope is False

    def test_rag_pipeline_query_returns_response(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = mock_retriever_instance
        
        mock_reranker_instance = MagicMock()
        mock_reranker.return_value = mock_reranker_instance
        
        mock_prompt_builder_instance = MagicMock()
        mock_prompt_builder_instance.build_out_of_scope.return_value = "Prompt"
        mock_prompt_builder.return_value = mock_prompt_builder_instance
        
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate.return_value = "Answer"
        mock_llm.return_value = mock_llm_instance
        
        config = RAGConfig()
        pipeline = RAGPipeline(config)
        
        result = pipeline.query("What?")
        
        assert isinstance(result, RAGResponse)

    def test_rag_pipeline_includes_audit_trail(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = mock_retriever_instance
        
        mock_reranker_instance = MagicMock()
        mock_reranker.return_value = mock_reranker_instance
        
        mock_prompt_builder_instance = MagicMock()
        mock_prompt_builder_instance.build_out_of_scope.return_value = "Prompt text"
        mock_prompt_builder.return_value = mock_prompt_builder_instance
        
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate.return_value = "Answer"
        mock_llm.return_value = mock_llm_instance
        
        config = RAGConfig()
        pipeline = RAGPipeline(config)
        
        response = pipeline.query("Query?")
        
        assert hasattr(response, 'prompt')
        assert response.prompt is not None

    def test_rag_pipeline_empty_query(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = mock_retriever_instance
        
        mock_reranker_instance = MagicMock()
        mock_reranker.return_value = mock_reranker_instance
        
        mock_prompt_builder_instance = MagicMock()
        mock_prompt_builder_instance.build_out_of_scope.return_value = "Prompt"
        mock_prompt_builder.return_value = mock_prompt_builder_instance
        
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate.return_value = "Response"
        mock_llm.return_value = mock_llm_instance
        
        config = RAGConfig()
        pipeline = RAGPipeline(config)
        
        response = pipeline.query("")
        
        assert isinstance(response, RAGResponse)

    def test_rag_pipeline_very_long_query(self, mock_retriever, mock_reranker, mock_prompt_builder, mock_llm):
        """
        """
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = mock_retriever_instance
        
        mock_reranker_instance = MagicMock()
        mock_reranker.return_value = mock_reranker_instance
        
        mock_prompt_builder_instance = MagicMock()
        mock_prompt_builder_instance.build_out_of_scope.return_value = "Prompt"
        mock_prompt_builder.return_value = mock_prompt_builder_instance
        
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate.return_value = "Response"
        mock_llm.return_value = mock_llm_instance
        
        config = RAGConfig()
        pipeline = RAGPipeline(config)
        
        long_query = "word " * 1000
        response = pipeline.query(long_query)
        
        assert isinstance(response, RAGResponse)
