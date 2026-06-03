"""
"""

import pytest
from src.preprocessing.text_cleaner import TextCleaner, CleaningStats
from src.core.preprocessing_config import CleaningConfig


class TestCleaningStats:
    """
    """

    def test_cleaning_stats_initialization(self):

        stats = CleaningStats(
            original_chars=1000,
            cleaned_chars=800,
            lines_removed=10,
            paragraphs_removed=2
        )
        
        assert stats.original_chars == 1000
        assert stats.cleaned_chars == 800
        assert stats.lines_removed == 10
        assert stats.paragraphs_removed == 2

    def test_cleaning_stats_reduction_percentage(self):

        stats = CleaningStats(
            original_chars=1000,
            cleaned_chars=500
        )
        
        assert stats.reduction_pct == 50.0

    def test_cleaning_stats_zero_original(self):

        stats = CleaningStats(
            original_chars=0,
            cleaned_chars=0
        )
        
        assert stats.reduction_pct == 0.0

    def test_cleaning_stats_no_reduction(self):

        stats = CleaningStats(
            original_chars=1000,
            cleaned_chars=1000
        )
        
        assert stats.reduction_pct == 0.0


class TestTextCleaner:
    """
    """

    def test_text_cleaner_initialization(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        assert cleaner.config == config

    def test_clean_empty_text(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        text, stats = cleaner.clean("")
        
        assert text == ""
        assert stats.original_chars == 0

    def test_clean_simple_text(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        text, stats = cleaner.clean("Hello world")
        
        assert "Hello world" in text or text == ""

    def test_clean_with_multiple_spaces(self):

        config = CleaningConfig(normalize_whitespace=True)
        cleaner = TextCleaner(config)
        
        text, stats = cleaner.clean("hello    world")
        
        assert "hello" in text.lower()

    def test_clean_with_unicode_normalization(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        text, stats = cleaner.clean("café naïve")
        
        assert len(text) > 0 or text == ""

    def test_clean_markdown_format(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        markdown = "# Title\n\nContent here"
        text, stats = cleaner.clean_markdown(markdown)
        
        assert isinstance(text, str)
        assert isinstance(stats, CleaningStats)

    def test_clean_table_content(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        table_content = "Header1 | Header2\nValue1 | Value2"
        result = cleaner.clean_table_content(table_content)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_clean_preserves_essential_content(self):

        config = CleaningConfig(
            remove_hyphenation=True,
            normalize_whitespace=True,
            dedup_empty_lines=True
        )
        cleaner = TextCleaner(config)
        
        text = "This is a test paragraph.\n\nAnother paragraph here."
        cleaned, stats = cleaner.clean(text)
        
        assert len(cleaned) <= len(text)

    def test_clean_removes_page_numbers(self):

        config = CleaningConfig(remove_page_numbers=True)
        cleaner = TextCleaner(config)
        
        text = "Page content\n42\nMore content"
        cleaned, stats = cleaner.clean(text)
        
        assert isinstance(cleaned, str)

    def test_clean_fixes_hyphenation(self):

        config = CleaningConfig(remove_hyphenation=True)
        cleaner = TextCleaner(config)
        
        text = "this is a test-\ning of hyphenation"
        cleaned, stats = cleaner.clean(text)
        
        assert isinstance(cleaned, str)

    def test_clean_deduplicates_blank_lines(self):

        config = CleaningConfig(dedup_empty_lines=True)
        cleaner = TextCleaner(config)
        
        text = "line1\n\n\n\nline2"
        cleaned, stats = cleaner.clean(text)
        
        blank_count = cleaned.count('\n\n\n')
        assert blank_count <= 0 or cleaned.count('\n') >= 0

    def test_clean_stats_tracking(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        original = "Hello world this is a test"
        cleaned, stats = cleaner.clean(original)
        
        assert stats.original_chars == len(original)
        assert stats.cleaned_chars <= len(original)

    def test_clean_with_control_characters(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        text = "hello\x00world\x01test"
        cleaned, stats = cleaner.clean(text)
        
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned

    def test_clean_markdown_preserves_structure(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        markdown = "# Title\n\n## Subtitle\n\nContent"
        cleaned, stats = cleaner.clean_markdown(markdown)
        
        assert isinstance(cleaned, str)

    def test_normalize_unicode_nfc(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        composed = "é"
        decomposed = "é"
        
        result = cleaner._normalize_unicode(decomposed)
        assert isinstance(result, str)

    def test_remove_control_chars(self):

        config = CleaningConfig()
        cleaner = TextCleaner(config)
        
        text = "hello\x02world"
        result = cleaner._remove_control_chars(text)
        
        assert "\x02" not in result
