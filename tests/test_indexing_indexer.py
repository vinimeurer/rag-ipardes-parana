import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.indexing.indexer import Indexer
from src.core.indexing_config import IndexingConfig


@patch('src.indexing.indexer.chromadb.PersistentClient')
class TestIndexer:

    def test_indexer_initialization(self, mock_chroma_client):

        mock_client = MagicMock()
        mock_chroma_client.return_value = mock_client

        config = IndexingConfig()
        indexer = Indexer(config)

        assert indexer.config == config
        assert indexer.logger is not None

    def test_run_pipeline_empty_chunks(self, mock_chroma_client):

        mock_client = MagicMock()
        mock_collection = MagicMock()

        mock_chroma_client.return_value = mock_client
        mock_client.delete_collection.side_effect = Exception("not found")
        mock_client.create_collection.return_value = mock_collection

        config = IndexingConfig()
        indexer = Indexer(config)

        with patch.object(Indexer, "_load_chunks", return_value=[]):

            result = indexer.run()

            assert result == 0
            mock_collection.add.assert_not_called()

    def test_run_pipeline_with_chunks(self, mock_chroma_client):

        mock_client = MagicMock()
        mock_collection = MagicMock()

        mock_chroma_client.return_value = mock_client
        mock_client.delete_collection.side_effect = Exception("not found")
        mock_client.create_collection.return_value = mock_collection

        fake_chunks = [
            {
                "chunk_id": "1",
                "embedding": [0.1, 0.2],
                "content": "text 1",
                "document": "doc",
                "page": 1,
                "sections": ["A"],
                "type": "text",
                "token_count": 10,
                "is_auxiliary": False,
                "caption": None
            },
            {
                "chunk_id": "2",
                "embedding": [0.3, 0.4],
                "content": "text 2",
                "document": "doc",
                "page": 2,
                "sections": ["B"],
                "type": "text",
                "token_count": 20,
                "is_auxiliary": False,
                "caption": "caption"
            }
        ]

        with patch.object(Indexer, "_load_chunks", return_value=fake_chunks):

            indexer = Indexer(IndexingConfig())
            result = indexer.run()

            assert result == 2
            mock_collection.add.assert_called_once()

    def test_load_chunks_real_file(self, mock_chroma_client):

        indexer = Indexer(IndexingConfig())

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "chunks.jsonl"

            chunk = {
                "chunk_id": "1",
                "embedding": [0.1, 0.2],
                "content": "hello"
            }

            path.write_text(json.dumps(chunk), encoding="utf-8")

            result = indexer._load_chunks(path)

            assert len(result) == 1
            assert result[0]["chunk_id"] == "1"

    def test_prepare_collection_creates_new_collection(self, mock_chroma_client):

        mock_client = MagicMock()
        mock_collection = MagicMock()

        mock_chroma_client.return_value = mock_client
        mock_client.delete_collection.return_value = None
        mock_client.create_collection.return_value = mock_collection

        indexer = Indexer(IndexingConfig())

        result = indexer._prepare_collection()

        assert result == mock_collection
        mock_client.create_collection.assert_called_once()

    def test_prepare_collection_handles_missing_collection(self, mock_chroma_client):

        mock_client = MagicMock()

        mock_chroma_client.return_value = mock_client
        mock_client.delete_collection.side_effect = Exception("does not exist")
        mock_client.create_collection.return_value = MagicMock()

        indexer = Indexer(IndexingConfig())

        result = indexer._prepare_collection()

        assert result is not None
        mock_client.create_collection.assert_called_once()

    def test_insert_batches_single_batch(self, mock_chroma_client):

        mock_client = MagicMock()
        mock_collection = MagicMock()

        mock_chroma_client.return_value = mock_client

        chunks = [
            {
                "chunk_id": "1",
                "embedding": [0.1],
                "content": "a",
                "document": "doc",
                "page": 1,
                "sections": [],
                "type": "text",
                "token_count": 1,
                "is_auxiliary": False,
                "caption": None
            }
        ]

        indexer = Indexer(IndexingConfig())

        result = indexer._insert_batches(chunks, mock_collection)

        assert result == 1
        mock_collection.add.assert_called_once()

    def test_build_metadata(self, mock_chroma_client):

        indexer = Indexer(IndexingConfig())

        chunk = {
            "document": "doc",
            "page": 3,
            "sections": ["A", "B", "C"],
            "type": "text",
            "token_count": 15,
            "is_auxiliary": True,
            "caption": None
        }

        meta = indexer._build_metadata(chunk)

        assert meta["document"] == "doc"
        assert meta["page"] == 3
        assert meta["sections"] == "A > B > C"
        assert meta["caption"] == ""
        assert meta["is_auxiliary"] is True