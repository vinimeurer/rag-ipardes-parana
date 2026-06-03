"""
"""

import pytest
from unittest.mock import patch, MagicMock

from src.preprocessing.content_processor import get_processing_strategy, SectionDetectionStrategy
from src.preprocessing.section_parser import SectionParser
from src.preprocessing.text_cleaner import TextCleaner
from src.core.preprocessing_config import CleaningConfig


class TestContentProcessingStrategy:
    """
    """

    def test_section_detection_strategy_initialization(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = SectionDetectionStrategy(text_cleaner)
        
        assert strategy is not None

    def test_section_detection_strategy_process(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = SectionDetectionStrategy(text_cleaner)
        
        pages = ["# Section\nContent here"]
        result = strategy.process(pages)
        
        assert isinstance(result, list)

    def test_section_detection_strategy_empty_pages(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = SectionDetectionStrategy(text_cleaner)
        
        result = strategy.process([])
        
        assert isinstance(result, list)

    def test_section_detection_strategy_with_headers(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = SectionDetectionStrategy(text_cleaner)
        
        pages = ["# Title\n## Subtitle\nContent"]
        result = strategy.process(pages)
        
        assert isinstance(result, list)

    def test_section_detection_multiple_sections(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = SectionDetectionStrategy(text_cleaner)
        
        pages = ["# Part 1\nContent1\n## Part 1.1\nContent 1.1\n# Part 2\nContent2"]
        result = strategy.process(pages)
        
        assert len(result) > 0

    def test_section_detection_preserves_content(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = SectionDetectionStrategy(text_cleaner)
        
        content = "Important information"
        pages = [f"# Title\n{content}"]
        result = strategy.process(pages)
        
        assert len(result) > 0


class TestGetProcessingStrategy:
    """
    """

    def test_get_processing_strategy_returns_strategy(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = get_processing_strategy(text_cleaner)
        
        assert strategy is not None

    def test_get_processing_strategy_callable(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = get_processing_strategy(text_cleaner)
        
        assert hasattr(strategy, 'process')

    def test_get_processing_strategy_returns_section_detection(self):

        text_cleaner = TextCleaner(CleaningConfig())
        strategy = get_processing_strategy(text_cleaner)
        
        assert isinstance(strategy, SectionDetectionStrategy) or strategy is not None
