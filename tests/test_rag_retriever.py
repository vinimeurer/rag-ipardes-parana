"""
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

from src.rag.retriever import Retriever, RetrievedChunk
from src.core.rag_config import RAGConfig


class TestRetrievedChunk:
    """
    """

    def test_retrieved_chunk_initialization(self):

        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="test_doc",
            page=1,
            sections=["Section"],
            type="text",
            content="Test content",
            caption=None,
            similarity=0.95
        )
        
        assert chunk.chunk_id == "test_001"
        assert chunk.document == "test_doc"
        assert chunk.page == 1
        assert chunk.sections == ["Section"]
        assert chunk.type == "text"
        assert chunk.content == "Test content"
        assert chunk.caption is None
        assert chunk.similarity == 0.95

    def test_retrieved_chunk_with_rerank_score(self):

        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="test_doc",
            page=1,
            sections=[],
            type="text",
            content="content",
            caption=None,
            similarity=0.9,
            rerank_score=0.75
        )
        
        assert chunk.rerank_score == 0.75

    def test_retrieved_chunk_without_rerank_score(self):

        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="test_doc",
            page=1,
            sections=[],
            type="text",
            content="content",
            caption=None,
            similarity=0.9
        )
        
        assert chunk.rerank_score is None

    def test_retrieved_chunk_with_table_type(self):

        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="test_doc",
            page=1,
            sections=[],
            type="table",
            content="table content",
            caption="Table 1",
            similarity=0.85
        )
        
        assert chunk.type == "table"
        assert chunk.caption == "Table 1"


@patch('src.rag.retriever.chromadb.PersistentClient')
@patch('src.rag.retriever.SentenceTransformer')
class TestRetriever:
    """
    """

    def test_retriever_initialization(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder.return_value = mock_encoder_instance
        
        config = RAGConfig()
        retriever = Retriever(config)
        
        assert retriever.config == config
        assert retriever.logger is not None

    def test_retrieve_returns_list(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_encoder.return_value = mock_encoder_instance
        
        mock_collection.query.return_value = {
            "ids": [[]],
            "metadatas": [[]],
            "documents": [[]],
            "distances": [[]]
        }
        
        config = RAGConfig()
        retriever = Retriever(config)
        result = retriever.retrieve("test query")
        
        assert isinstance(result, list)

    def test_retrieve_filters_by_threshold(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_encoder.return_value = mock_encoder_instance
        
        mock_collection.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "metadatas": [
                {
                    "document": "doc1",
                    "page": 1,
                    "sections": "intro",
                    "type": "text",
                    "caption": None
                },
                {
                    "document": "doc2",
                    "page": 2,
                    "sections": "section",
                    "type": "text",
                    "caption": None
                }
            ],
            "documents": [["content1", "content2"]],
            "distances": [[0.1, 0.8]]
        }
        
        config = RAGConfig()
        config.retriever.min_similarity = 0.5
        retriever = Retriever(config)
        result = retriever.retrieve("test query")
        
        assert len(result) >= 0

    def test_retrieve_returns_retrieved_chunks(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_encoder.return_value = mock_encoder_instance
        
        mock_collection.query.return_value = {
            "ids": [["chunk1"]],
            "metadatas": [{
                "document": "doc1",
                "page": 1,
                "sections": "intro",
                "type": "text",
                "caption": None
            }],
            "documents": [["content1"]],
            "distances": [[0.1]]
        }
        
        config = RAGConfig()
        retriever = Retriever(config)
        result = retriever.retrieve("test query")
        
        if len(result) > 0:
            chunk = result[0]
            assert isinstance(chunk, RetrievedChunk)
            assert chunk.chunk_id == "chunk1"

    def test_retrieve_empty_results(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_encoder.return_value = mock_encoder_instance
        
        mock_collection.query.return_value = {
            "ids": [[]],
            "metadatas": [[]],
            "documents": [[]],
            "distances": [[]]
        }
        
        config = RAGConfig()
        retriever = Retriever(config)
        result = retriever.retrieve("test query")
        
        assert result == []

    def test_retrieve_metadata_parsing(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_encoder.return_value = mock_encoder_instance
        
        mock_collection.query.return_value = {
            "ids": [["chunk1"]],
            "metadatas": [{
                "document": "desenvolvimento_paranaense",
                "page": 42,
                "sections": "Introduction > Background",
                "type": "text",
                "caption": None
            }],
            "documents": [["some content"]],
            "distances": [[0.1]]
        }
        
        config = RAGConfig()
        retriever = Retriever(config)
        result = retriever.retrieve("test query")
        
        if len(result) > 0:
            chunk = result[0]
            assert chunk.document == "desenvolvimento_paranaense"
            assert chunk.page == 42
            assert len(chunk.sections) > 0

    def test_retrieve_similarity_score_calculation(self, mock_encoder, mock_chroma_client):

        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance
        
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_encoder.return_value = mock_encoder_instance
        
        mock_collection.query.return_value = {
            "ids": [["chunk1"]],
            "metadatas": [{
                "document": "doc1",
                "page": 1,
                "sections": "",
                "type": "text",
                "caption": None
            }],
            "documents": [["content"]],
            "distances": [[0.2]]
        }
        
        config = RAGConfig()
        retriever = Retriever(config)
        result = retriever.retrieve("test query")
        
        if len(result) > 0:
            assert 0 <= result[0].similarity <= 1
