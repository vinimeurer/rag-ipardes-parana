"""
"""

import pytest
from unittest.mock import MagicMock, patch

from src.rag.prompt_builder import PromptBuilder, SYSTEM_PROMPT, SOURCE_LABELS, SOURCE_SHORT_LABELS
from src.rag.retriever import RetrievedChunk


class TestPromptBuilder:
    """
    """

    def test_prompt_builder_initialization(self):
        """
        """
        builder = PromptBuilder()
        assert builder is not None

    def test_build_basic_prompt(self):
        """
        """
        builder = PromptBuilder()
        query = "What is development?"
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=1,
                sections=["Introduction"],
                type="text",
                content="Development refers to economic growth",
                caption=None,
                similarity=0.95
            )
        ]
        
        prompt = builder.build(query, chunks)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert "Development refers" in prompt

    def test_build_includes_system_prompt(self):
        """
        """
        builder = PromptBuilder()
        prompt = builder.build("test query", [])
        
        assert SYSTEM_PROMPT in prompt

    def test_build_out_of_scope(self):
        """
        """
        builder = PromptBuilder()
        query = "What is not covered?"
        
        prompt = builder.build_out_of_scope(query)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert "não há informação" in prompt or "not found" in prompt or SYSTEM_PROMPT in prompt

    def test_format_sources_empty(self):
        """
        """
        builder = PromptBuilder()
        result = builder.format_sources([])
        
        assert isinstance(result, str)
        assert "nenhum" in result.lower() or "sem" in result.lower() or "não" in result.lower()

    def test_format_sources_single_chunk(self):
        """
        """
        builder = PromptBuilder()
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=5,
                sections=["Development", "Trends"],
                type="text",
                content="Development is important",
                caption=None,
                similarity=0.9
            )
        ]
        
        result = builder.format_sources(chunks)
        
        assert isinstance(result, str)
        assert "Development is important" in result or "página" in result or "page" in result

    def test_format_sources_multiple_chunks(self):
        """
        """
        builder = PromptBuilder()
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=1,
                sections=["Intro"],
                type="text",
                content="First chunk",
                caption=None,
                similarity=0.95
            ),
            RetrievedChunk(
                chunk_id="test_002",
                document="analise_conjuntural",
                page=2,
                sections=["Analysis"],
                type="text",
                content="Second chunk",
                caption=None,
                similarity=0.85
            )
        ]
        
        result = builder.format_sources(chunks)
        
        assert "First chunk" in result or "[1]" in result
        assert "Second chunk" in result or "[2]" in result

    def test_format_sources_with_table(self):
        """
        """
        builder = PromptBuilder()
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=1,
                sections=[],
                type="table",
                content="Col1 | Col2\nA | B",
                caption="Data Table",
                similarity=0.9
            )
        ]
        
        result = builder.format_sources(chunks)
        
        assert isinstance(result, str)
        assert "Table" in result or "Tabela" in result or "Data Table" in result

    def test_format_sources_includes_page_number(self):
        """
        """
        builder = PromptBuilder()
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=42,
                sections=[],
                type="text",
                content="content",
                caption=None,
                similarity=0.9
            )
        ]
        
        result = builder.format_sources(chunks)
        
        assert "42" in result or "página" in result or "page" in result

    def test_format_sources_includes_similarity(self):
        """
        """
        builder = PromptBuilder()
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=1,
                sections=[],
                type="text",
                content="content",
                caption=None,
                similarity=0.8765
            )
        ]
        
        result = builder.format_sources(chunks)
        
        assert "0.8765" in result or "Similaridade" in result or "Similarity" in result

    def test_format_sources_with_rerank_score(self):
        """
        """
        builder = PromptBuilder()
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=1,
                sections=[],
                type="text",
                content="content",
                caption=None,
                similarity=0.9,
                rerank_score=0.75
            )
        ]
        
        result = builder.format_sources(chunks)
        
        assert "0.75" in result or "reranker" in result.lower()

    def test_format_location_with_sections(self):
        """
        """
        builder = PromptBuilder()
        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="desenvolvimento_paranaense",
            page=10,
            sections=["Chapter 1", "Section 2"],
            type="text",
            content="content",
            caption=None,
            similarity=0.9
        )
        
        location = builder._format_location(chunk)
        
        assert isinstance(location, str)
        assert "10" in location or "página" in location
        assert "Chapter 1" in location or "Section 2" in location or "seção" in location

    def test_format_location_without_sections(self):
        """
        """
        builder = PromptBuilder()
        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="desenvolvimento_paranaense",
            page=5,
            sections=[],
            type="text",
            content="content",
            caption=None,
            similarity=0.9
        )
        
        location = builder._format_location(chunk)
        
        assert "5" in location or "página" in location

    def test_build_with_multiple_chunks(self):
        """
        """
        builder = PromptBuilder()
        query = "What is the economic trend?"
        chunks = [
            RetrievedChunk(
                chunk_id="test_001",
                document="desenvolvimento_paranaense",
                page=1,
                sections=["Economy"],
                type="text",
                content="GDP grew by 3%",
                caption=None,
                similarity=0.95
            ),
            RetrievedChunk(
                chunk_id="test_002",
                document="analise_conjuntural",
                page=2,
                sections=["Trends"],
                type="text",
                content="Employment increased",
                caption=None,
                similarity=0.85
            )
        ]
        
        prompt = builder.build(query, chunks)
        
        assert query in prompt
        assert "GDP grew" in prompt or "Employment increased" in prompt

    def test_format_citation(self):
        """
        """
        builder = PromptBuilder()
        chunk = RetrievedChunk(
            chunk_id="test_001",
            document="desenvolvimento_paranaense",
            page=10,
            sections=["Intro"],
            type="text",
            content="content",
            caption=None,
            similarity=0.9
        )
        
        citation = builder._format_citation(chunk)
        
        assert isinstance(citation, str)
        assert "10" in citation or "p." in citation
        assert "(" in citation and ")" in citation

    def test_format_context_empty_chunks(self):
        """
        """
        builder = PromptBuilder()
        context = builder._format_context([])
        
        assert isinstance(context, str)
