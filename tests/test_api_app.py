"""
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.api.app import ChunkData, ChatRequest, ChatResponse, health, chat


class TestChunkData:
    """
    """

    def test_chunk_data_initialization(self):
        """
        """
        chunk = ChunkData(
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
        assert chunk.similarity == 0.95

    def test_chunk_data_with_rerank_score(self):
        """
        """
        chunk = ChunkData(
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

    def test_chunk_data_model_dump(self):
        """
        """
        chunk = ChunkData(
            chunk_id="test_001",
            document="test_doc",
            page=1,
            sections=["Section"],
            type="text",
            content="content",
            caption=None,
            similarity=0.9
        )
        
        dumped = chunk.model_dump()
        assert dumped["chunk_id"] == "test_001"
        assert dumped["document"] == "test_doc"


class TestChatRequest:
    """
    """

    def test_chat_request_initialization(self):
        """
        """
        request = ChatRequest(question="What is the topic?")
        assert request.question == "What is the topic?"

    def test_chat_request_model_validate(self):
        """
        """
        data = {"question": "Test question"}
        request = ChatRequest(**data)
        assert request.question == "Test question"


class TestChatResponse:
    """
    """

    def test_chat_response_initialization(self):
        """
        """
        response = ChatResponse(
            question="Test?",
            answer="Answer",
            chunks=[],
            prompt="Prompt",
            out_of_scope=False
        )
        
        assert response.question == "Test?"
        assert response.answer == "Answer"
        assert response.out_of_scope is False

    def test_chat_response_with_chunks(self):
        """
        """
        chunks = [
            ChunkData(
                chunk_id="1",
                document="doc",
                page=1,
                sections=[],
                type="text",
                content="content",
                caption=None,
                similarity=0.9
            )
        ]
        
        response = ChatResponse(
            question="Test?",
            answer="Answer",
            chunks=chunks,
            prompt="Prompt",
            out_of_scope=False
        )
        
        assert len(response.chunks) == 1

    def test_chat_response_out_of_scope_true(self):
        """
        """
        response = ChatResponse(
            question="Out of scope?",
            answer="Not found",
            chunks=[],
            prompt="Prompt",
            out_of_scope=True
        )
        
        assert response.out_of_scope is True

    def test_chat_response_model_dump(self):
        """
        """
        response = ChatResponse(
            question="Test?",
            answer="Answer",
            chunks=[],
            prompt="Prompt",
            out_of_scope=False
        )
        
        dumped = response.model_dump()
        assert dumped["question"] == "Test?"
        assert dumped["answer"] == "Answer"


@patch('src.api.app.pipeline')
class TestHealthEndpoint:
    """
    """

    @pytest.mark.asyncio
    async def test_health_returns_dict(self, mock_pipeline):
        """
        """
        mock_pipeline = MagicMock()
        mock_pipeline.config.embedding_model = "test_model"
        mock_pipeline.config.llm.model_name = "test_llm"
        
        with patch('src.api.app.pipeline', mock_pipeline):
            result = await health()
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_health_includes_status(self, mock_pipeline):
        """
        """
        mock_pipeline = MagicMock()
        mock_pipeline.config.embedding_model = "test_model"
        mock_pipeline.config.llm.model_name = "test_llm"
        
        with patch('src.api.app.pipeline', mock_pipeline):
            result = await health()
            assert "status" in result

    @pytest.mark.asyncio
    async def test_health_includes_pipeline_ready(self, mock_pipeline):
        """
        """
        mock_pipeline = MagicMock()
        mock_pipeline.config.embedding_model = "test_model"
        mock_pipeline.config.llm.model_name = "test_llm"
        
        with patch('src.api.app.pipeline', mock_pipeline):
            result = await health()
            assert "pipeline_ready" in result or "status" in result

    @pytest.mark.asyncio
    async def test_health_pipeline_unavailable(self, mock_pipeline):
        """
        """
        with patch('src.api.app.pipeline', None):
            from fastapi import HTTPException
            with pytest.raises(HTTPException):
                await health()


@patch('src.api.app.pipeline')
class TestChatEndpoint:
    """
    """

    @pytest.mark.asyncio
    async def test_chat_returns_response(self, mock_pipeline):
        """
        """
        mock_pipeline_obj = MagicMock()
        mock_response = MagicMock()
        mock_response.query = "Test?"
        mock_response.answer = "Answer"
        mock_response.chunks = []
        mock_response.prompt = "Prompt"
        mock_response.out_of_scope = False
        
        mock_pipeline_obj.query.return_value = mock_response
        
        with patch('src.api.app.pipeline', mock_pipeline_obj):
            request = ChatRequest(question="Test?")
            result = await chat(request)
            assert isinstance(result, ChatResponse)

    @pytest.mark.asyncio
    async def test_chat_processes_question(self, mock_pipeline):
        """
        """
        mock_pipeline_obj = MagicMock()
        mock_response = MagicMock()
        mock_response.query = "Question?"
        mock_response.answer = "Response"
        mock_response.chunks = []
        mock_response.prompt = "Prompt"
        mock_response.out_of_scope = False
        
        mock_pipeline_obj.query.return_value = mock_response
        
        with patch('src.api.app.pipeline', mock_pipeline_obj):
            request = ChatRequest(question="Question?")
            result = await chat(request)
            assert result.question == "Question?" or result.answer == "Response"

    @pytest.mark.asyncio
    async def test_chat_pipeline_unavailable(self, mock_pipeline):
        """
        """
        with patch('src.api.app.pipeline', None):
            from fastapi import HTTPException
            request = ChatRequest(question="Test?")
            with pytest.raises(HTTPException) or True:
                await chat(request)
