"""
"""

import pytest
from src.chunking.chunk_dataclass import Chunk


class TestChunk:
    """
    """

    def test_chunk_initialization(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=["Section 1", "Section 2"],
            type="text",
            content="This is test content",
            token_count=4,
            is_auxiliary=False,
            caption=None
        )
        assert chunk.chunk_id == "doc_000_00"
        assert chunk.document == "test_doc"
        assert chunk.page == 1
        assert chunk.sections == ["Section 1", "Section 2"]
        assert chunk.type == "text"
        assert chunk.content == "This is test content"
        assert chunk.token_count == 4
        assert chunk.is_auxiliary is False
        assert chunk.caption is None

    def test_chunk_with_caption(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=[],
            type="table",
            content="table content",
            token_count=2,
            caption="Table 1: Sales Data"
        )
        assert chunk.caption == "Table 1: Sales Data"
        assert chunk.type == "table"

    def test_chunk_is_auxiliary_true(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=[],
            type="text",
            content="content",
            token_count=1,
            is_auxiliary=True
        )
        assert chunk.is_auxiliary is True

    def test_chunk_to_dict(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=["Section 1"],
            type="text",
            content="content",
            token_count=1,
            is_auxiliary=False,
            caption=None
        )
        chunk_dict = chunk.to_dict()
        
        assert isinstance(chunk_dict, dict)
        assert chunk_dict["chunk_id"] == "doc_000_00"
        assert chunk_dict["document"] == "test_doc"
        assert chunk_dict["page"] == 1
        assert chunk_dict["sections"] == ["Section 1"]
        assert chunk_dict["type"] == "text"
        assert chunk_dict["content"] == "content"
        assert chunk_dict["token_count"] == 1
        assert chunk_dict["is_auxiliary"] is False
        assert chunk_dict["caption"] is None

    def test_chunk_to_dict_with_caption(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=[],
            type="table",
            content="table",
            token_count=2,
            caption="Table 1"
        )
        chunk_dict = chunk.to_dict()
        assert chunk_dict["caption"] == "Table 1"

    def test_chunk_to_dict_empty_sections(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=[],
            type="text",
            content="content",
            token_count=1
        )
        chunk_dict = chunk.to_dict()
        assert chunk_dict["sections"] == []

    def test_chunk_to_dict_multiple_sections(self):

        sections = ["Section 1", "Section 2", "Section 3"]
        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=sections,
            type="text",
            content="content",
            token_count=1
        )
        chunk_dict = chunk.to_dict()
        assert chunk_dict["sections"] == sections

    def test_chunk_with_zero_page(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=0,
            sections=[],
            type="text",
            content="content",
            token_count=1
        )
        assert chunk.page == 0

    def test_chunk_with_large_token_count(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=[],
            type="text",
            content="content",
            token_count=10000
        )
        assert chunk.token_count == 10000

    def test_chunk_with_empty_content(self):

        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=[],
            type="text",
            content="",
            token_count=0
        )
        assert chunk.content == ""
        assert chunk.token_count == 0

    def test_chunk_dataclass_fields(self):

        chunk = Chunk(
            chunk_id="test",
            document="doc",
            page=1,
            sections=[],
            type="text",
            content="content",
            token_count=1
        )
        
        assert hasattr(chunk, "chunk_id")
        assert hasattr(chunk, "document")
        assert hasattr(chunk, "page")
        assert hasattr(chunk, "sections")
        assert hasattr(chunk, "type")
        assert hasattr(chunk, "content")
        assert hasattr(chunk, "token_count")
        assert hasattr(chunk, "is_auxiliary")
        assert hasattr(chunk, "caption")

    def test_chunk_to_dict_is_json_serializable(self):

        import json
        chunk = Chunk(
            chunk_id="doc_000_00",
            document="test_doc",
            page=1,
            sections=["Section"],
            type="text",
            content="content",
            token_count=1
        )
        chunk_dict = chunk.to_dict()
        json_str = json.dumps(chunk_dict, ensure_ascii=False)
        assert json_str is not None
        decoded = json.loads(json_str)
        assert decoded["chunk_id"] == "doc_000_00"
