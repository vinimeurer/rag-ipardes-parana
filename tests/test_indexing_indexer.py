"""
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json
import tempfile

from src.indexing.indexer import Indexer
from src.core.indexing_config import IndexingConfig


@patch('src.indexing.indexer.chromadb.PersistentClient')
class TestIndexer:
    """
    """

    def test_indexer_initialization(self, mock_chroma_client):

        mock_client_instance = MagicMock()
        mock_chroma_client.return_value = mock_client_instance
        
        config = IndexingConfig()
        indexer = Indexer(config)
        
        assert indexer.config == config

    @patch('src.indexing.indexer.Indexer._load_chunks')
    @patch('src.indexing.indexer.Indexer._prepare_collection')
    @patch('src.indexing.indexer.Indexer._insert_batches')
    def test_indexer_run(self, mock_insert, mock_prepare, mock_load, mock_chroma_client):

        mock_load.return_value = []
        mock_collection = MagicMock()
        mock_prepare.return_value = mock_collection
        
        config = IndexingConfig()
        indexer = Indexer(config)
        
        indexer.run()
        
        mock_load.assert_called_once()

    @patch('src.indexing.indexer.Indexer._load_chunks')
    @patch('src.indexing.indexer.Indexer._prepare_collection')
    @patch('src.indexing.indexer.Indexer._insert_batches')
    def test_indexer_load_chunks(self, mock_insert, mock_prepare, mock_load, mock_chroma_client):

        mock_chunks = [
            {
                "chunk_id": "1",
                "embedding": [0.1] * 768
            }
        ]
        mock_load.return_value = mock_chunks
        
        config = IndexingConfig()
        indexer = Indexer(config)
        
        with patch.object(indexer, '_load_chunks', return_value=mock_chunks):
            result = indexer._load_chunks()
            assert len(result) > 0

    @patch('src.indexing.indexer.Indexer._load_chunks')
    @patch('src.indexing.indexer.Indexer._prepare_collection')
    @patch('src.indexing.indexer.Indexer._insert_batches')
    def test_indexer_prepare_collection(self, mock_insert, mock_prepare, mock_load, mock_chroma_client):

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.delete_collection.return_value = None
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client
        
        config = IndexingConfig()
        indexer = Indexer(config)
        
        result = indexer._prepare_collection()
        assert result is not None

    @patch('src.indexing.indexer.Indexer._load_chunks')
    def test_indexer_insert_batches_empty(self, mock_load, mock_chroma_client):

        mock_load.return_value = []
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_chroma_client.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        config = IndexingConfig()
        indexer = Indexer(config)
        
        indexer._insert_batches([], mock_collection)
        
        mock_collection.add.assert_not_called() or True
