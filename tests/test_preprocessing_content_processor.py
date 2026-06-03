import pytest
from src.preprocessing.content_processor import (
    SectionDetectionStrategy,
    PageFallbackStrategy,
    get_processing_strategy,
)
from src.core.preprocessing_config import CleaningConfig


class TestContentProcessingStrategy:

    def test_section_detection_strategy_initialization(self):
        strategy = SectionDetectionStrategy()
        assert strategy.cleaner is not None

    def test_section_detection_empty_input(self):
        strategy = SectionDetectionStrategy()

        result = strategy.process("doc", [])
        assert result == []

    def test_section_detection_basic_flow(self):
        strategy = SectionDetectionStrategy()

        pages_data = [
            {
                "page_number": 1,
                "text": "# Title\nSome content here"
            }
        ]

        result = strategy.process("doc", pages_data)

        assert isinstance(result, list)
        assert len(result) >= 1

        item = result[0]
        assert item["document"] == "doc"
        assert item["page"] == 1
        assert item["type"] == "text"
        assert "content" in item
        assert "sections" in item

    def test_section_detection_multiple_lines(self):
        strategy = SectionDetectionStrategy()

        pages_data = [
            {
                "page_number": 1,
                "text": "# A\nline1\nline2\n## B\nline3"
            }
        ]

        result = strategy.process("doc", pages_data)

        assert len(result) >= 1

        assert all("content" in r for r in result)

    def test_section_detection_ignores_empty_text(self):
        strategy = SectionDetectionStrategy()

        pages_data = [
            {"page_number": 1, "text": "   \n   "}
        ]

        result = strategy.process("doc", pages_data)

        assert result == []


class TestPageFallbackStrategy:

    def test_fallback_strategy_basic(self):
        strategy = PageFallbackStrategy()

        pages_data = [
            {
                "page_number": 2,
                "text": "Simple content"
            }
        ]

        result = strategy.process("doc", pages_data)

        assert len(result) == 1
        assert result[0]["sections"] == ["pagina_2"]
        assert result[0]["type"] == "text"

    def test_fallback_strategy_empty_input(self):
        strategy = PageFallbackStrategy()

        assert strategy.process("doc", []) == []


class TestGetProcessingStrategy:

    def test_returns_section_strategy_default(self):
        strategy = get_processing_strategy("any_doc")

        assert isinstance(strategy, SectionDetectionStrategy)

    def test_returns_fallback_for_specific_doc(self):
        strategy = get_processing_strategy("analise_conjuntural")

        assert isinstance(strategy, PageFallbackStrategy)

    def test_strategy_has_process_method(self):
        strategy = get_processing_strategy("doc")

        assert callable(strategy.process)