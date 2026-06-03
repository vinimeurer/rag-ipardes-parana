"""
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.chunking.chunker import Chunker
from src.chunking.chunk_dataclass import Chunk
from src.core.chunking_config import ChunkingConfig


class TestChunker:
    """
    """

    def test_chunker_initialization(self):

        chunker = Chunker()
        assert chunker.config is not None
        assert chunker.splitter is not None
        assert chunker.logger is not None

    def test_chunker_initialization_with_config(self):

        config = ChunkingConfig()
        chunker = Chunker(config=config)
        assert chunker.config == config

    def test_chunker_save_creates_file(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunks.jsonl"
            
            chunk1 = Chunk(
                chunk_id="test_001_00",
                document="test_doc",
                page=1,
                sections=["Intro"],
                type="text",
                content="First chunk",
                token_count=2,
                is_auxiliary=False,
                caption=None
            )
            chunk2 = Chunk(
                chunk_id="test_001_01",
                document="test_doc",
                page=1,
                sections=["Intro"],
                type="text",
                content="Second chunk",
                token_count=2,
                is_auxiliary=False,
                caption=None
            )
            
            chunker = Chunker()
            result = chunker.save([chunk1, chunk2], output_path=output_path)
            
            assert output_path.exists()
            assert result == output_path

    def test_chunker_save_jsonl_format(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunks.jsonl"
            
            chunk = Chunk(
                chunk_id="test_001_00",
                document="test_doc",
                page=1,
                sections=[],
                type="text",
                content="content",
                token_count=1
            )
            
            chunker = Chunker()
            chunker.save([chunk], output_path=output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                line = f.readline()
                data = json.loads(line)
                assert data["chunk_id"] == "test_001_00"

    def test_chunker_save_multiple_chunks(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunks.jsonl"
            
            chunks = [
                Chunk(
                    chunk_id=f"test_00{i}_00",
                    document="test_doc",
                    page=1,
                    sections=[],
                    type="text",
                    content=f"content {i}",
                    token_count=2
                )
                for i in range(5)
            ]
            
            chunker = Chunker()
            chunker.save(chunks, output_path=output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 5

    def test_chunker_save_creates_parent_directory(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "chunks.jsonl"
            
            chunk = Chunk(
                chunk_id="test_001_00",
                document="test_doc",
                page=1,
                sections=[],
                type="text",
                content="content",
                token_count=1
            )
            
            chunker = Chunker()
            result = chunker.save([chunk], output_path=output_path)
            
            assert output_path.parent.exists()
            assert result == output_path

    def test_chunker_save_empty_chunks(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunks.jsonl"
            
            chunker = Chunker()
            result = chunker.save([], output_path=output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
                assert content == "" or content.count('\n') == 0

    def test_chunker_save_preserves_unicode(self):

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunks.jsonl"
            
            chunk = Chunk(
                chunk_id="test_001_00",
                document="doc",
                page=1,
                sections=["Seção"],
                type="text",
                content="Conteúdo com acentuação",
                token_count=4
            )
            
            chunker = Chunker()
            chunker.save([chunk], output_path=output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                line = f.readline()
                data = json.loads(line)
                assert "acentuação" in data["content"]

    def test_chunker_chunk_text_item_basic(self):

        chunker = Chunker()
        item = {
            "type": "text",
            "content": "word1 word2 word3 word4 word5",
            "page": 1,
            "sections": ["Section"]
        }
        
        result = chunker._chunk_text_item(item, "doc_key", 0)
        assert len(result) > 0
        assert all(isinstance(c, Chunk) for c in result)

    def test_chunker_chunk_text_item_empty_content(self):

        chunker = Chunker()
        item = {
            "type": "text",
            "content": "",
            "page": 1,
            "sections": []
        }
        
        result = chunker._chunk_text_item(item, "doc_key", 0)
        assert len(result) == 0

    def test_chunker_chunk_text_item_whitespace_only(self):

        chunker = Chunker()
        item = {
            "type": "text",
            "content": "   \n\t  ",
            "page": 1,
            "sections": []
        }
        
        result = chunker._chunk_text_item(item, "doc_key", 0)
        assert len(result) == 0

    def test_chunker_chunk_table_item_basic(self):

        chunker = Chunker()
        item = {
            "type": "table",
            "content": "Header1 | Header2\nValue1 | Value2",
            "page": 1,
            "sections": [],
            "is_auxiliary": False,
            "caption": "Table 1"
        }
        
        result = chunker._chunk_table_item(item, "doc_key", 0)
        assert result is not None
        assert isinstance(result, Chunk)

    def test_chunker_chunk_table_item_empty_content(self):

        chunker = Chunker()
        item = {
            "type": "table",
            "content": "",
            "page": 1,
            "sections": [],
            "caption": None
        }
        
        result = chunker._chunk_table_item(item, "doc_key", 0)
        assert result is None

    def test_chunker_chunk_table_item_preserves_structure(self):

        chunker = Chunker()
        table_content = "Header1 | Header2\nValue1 | Value2"
        item = {
            "type": "table",
            "content": table_content,
            "page": 1,
            "sections": [],
            "caption": None
        }
        
        result = chunker._chunk_table_item(item, "doc_key", 0)
        if result:
            assert table_content in result.content

    def test_chunker_chunk_id_generation(self):

        chunker = Chunker()
        item = {
            "type": "text",
            "content": "word1 word2 word3 word4 word5",
            "page": 1,
            "sections": []
        }
        
        result = chunker._chunk_text_item(item, "mydoc", 5)
        for chunk in result:
            assert "mydoc" in chunk.chunk_id
            assert "005" in chunk.chunk_id

    def test_chunker_preserves_sections(self):

        chunker = Chunker()
        sections = ["Introduction", "Background"]
        item = {
            "type": "text",
            "content": "word1 word2 word3 word4 word5",
            "page": 1,
            "sections": sections
        }
        
        result = chunker._chunk_text_item(item, "doc", 0)
        for chunk in result:
            assert chunk.sections == sections

    def test_chunker_preserves_page_number(self):

        chunker = Chunker()
        item = {
            "type": "text",
            "content": "word1 word2 word3 word4 word5",
            "page": 42,
            "sections": []
        }
        
        result = chunker._chunk_text_item(item, "doc", 0)
        for chunk in result:
            assert chunk.page == 42
