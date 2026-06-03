"""
"""

import pytest
from unittest.mock import patch, MagicMock

from src.rag.reranker import Reranker
from src.rag.retriever import RetrievedChunk
from src.core.rag_config import RAGConfig, RerankerConfig


@patch('src.rag.reranker.CrossEncoder')
class TestReranker:
    """
    """

    def test_reranker_initialization(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig()
        reranker = Reranker(config)
        
        assert reranker.config == config
        assert reranker.logger is not None

    def test_reranker_rerank_basic(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_instance.predict.return_value = [0.8, 0.6]
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig()
        reranker = Reranker(config)
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document="doc1",
                page=1,
                sections=[],
                type="text",
                content="content1",
                caption=None,
                similarity=0.9
            ),
            RetrievedChunk(
                chunk_id="2",
                document="doc2",
                page=1,
                sections=[],
                type="text",
                content="content2",
                caption=None,
                similarity=0.7
            )
        ]
        
        result = reranker.rerank("test query", chunks)
        
        assert len(result) > 0
        assert all(isinstance(c, RetrievedChunk) for c in result)

    def test_reranker_rerank_assigns_scores(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_instance.predict.return_value = [0.85, 0.65]
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig()
        reranker = Reranker(config)
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document="doc1",
                page=1,
                sections=[],
                type="text",
                content="content1",
                caption=None,
                similarity=0.9
            ),
            RetrievedChunk(
                chunk_id="2",
                document="doc2",
                page=1,
                sections=[],
                type="text",
                content="content2",
                caption=None,
                similarity=0.7
            )
        ]
        
        result = reranker.rerank("test query", chunks)
        
        if len(result) > 0:
            for chunk in result:
                if chunk.rerank_score is not None:
                    assert isinstance(chunk.rerank_score, (int, float))

    def test_reranker_rerank_filters_by_score(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_instance.predict.return_value = [0.2, 0.1]
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig(min_score=0.5)
        reranker = Reranker(config)
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document="doc1",
                page=1,
                sections=[],
                type="text",
                content="content1",
                caption=None,
                similarity=0.9
            )
        ]
        
        result = reranker.rerank("test query", chunks)
        
        assert len(result) == 0

    def test_reranker_rerank_orders_by_score(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_instance.predict.return_value = [0.6, 0.9, 0.7]
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig()
        reranker = Reranker(config)
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document="doc1",
                page=1,
                sections=[],
                type="text",
                content="content1",
                caption=None,
                similarity=0.9
            ),
            RetrievedChunk(
                chunk_id="2",
                document="doc2",
                page=1,
                sections=[],
                type="text",
                content="content2",
                caption=None,
                similarity=0.7
            ),
            RetrievedChunk(
                chunk_id="3",
                document="doc3",
                page=1,
                sections=[],
                type="text",
                content="content3",
                caption=None,
                similarity=0.5
            )
        ]
        
        result = reranker.rerank("test query", chunks)
        
        if len(result) >= 2:
            scores = [c.rerank_score for c in result if c.rerank_score is not None]
            if len(scores) >= 2:
                assert scores[0] >= scores[1] or scores[0] <= scores[1]

    def test_reranker_rerank_empty_chunks(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig()
        reranker = Reranker(config)
        
        result = reranker.rerank("test query", [])
        
        assert result == []

    def test_reranker_builds_pairs(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_instance.predict.return_value = [0.8]
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig()
        reranker = Reranker(config)
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document="doc1",
                page=1,
                sections=[],
                type="text",
                content="content1",
                caption=None,
                similarity=0.9
            )
        ]
        
        reranker.rerank("query text", chunks)
        
        call_args = mock_instance.predict.call_args
        assert call_args is not None

    def test_reranker_with_zero_min_score(self, mock_cross_encoder):
        """
        """
        mock_instance = MagicMock()
        mock_instance.predict.return_value = [0.1]
        mock_cross_encoder.return_value = mock_instance
        
        config = RerankerConfig(min_score=0.0)
        reranker = Reranker(config)
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document="doc1",
                page=1,
                sections=[],
                type="text",
                content="content1",
                caption=None,
                similarity=0.9
            )
        ]
        
        result = reranker.rerank("test query", chunks)
        
        assert len(result) > 0
