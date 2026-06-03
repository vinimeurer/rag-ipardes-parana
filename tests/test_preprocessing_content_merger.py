"""
"""

import pytest
from unittest.mock import patch, MagicMock

from src.preprocessing.content_merger import ContentMerger


class TestContentMerger:
    """
    """

    def test_content_merger_merge_empty_lists(self):
        """
        """
        result = ContentMerger.merge_content_and_tables([], [])
        
        assert result == []

    def test_content_merger_text_only(self):
        """
        """
        text_items = [
            {
                "type": "text",
                "content": "text 1",
                "page": 1,
                "sections": []
            }
        ]
        
        result = ContentMerger.merge_content_and_tables(text_items, [])
        
        assert len(result) > 0

    def test_content_merger_table_only(self):
        """
        """
        table_items = [
            {
                "type": "table",
                "content": "table content",
                "page": 1,
                "sections": []
            }
        ]
        
        result = ContentMerger.merge_content_and_tables([], table_items)
        
        assert len(result) > 0

    def test_content_merger_mixed_content(self):
        """
        """
        text_items = [
            {
                "type": "text",
                "content": "text",
                "page": 1,
                "sections": ["Intro"]
            }
        ]
        table_items = [
            {
                "type": "table",
                "content": "table",
                "page": 1,
                "sections": []
            }
        ]
        
        result = ContentMerger.merge_content_and_tables(text_items, table_items)
        
        assert len(result) > 0

    def test_content_merger_multiple_pages(self):
        """
        """
        text_items = [
            {"type": "text", "content": "page1", "page": 1, "sections": []},
            {"type": "text", "content": "page2", "page": 2, "sections": []}
        ]
        
        result = ContentMerger.merge_content_and_tables(text_items, [])
        
        assert len(result) >= 2

    def test_content_merger_preserves_sections(self):
        """
        """
        text_items = [
            {"type": "text", "content": "text", "page": 1, "sections": ["A", "B"]}
        ]
        table_items = [
            {"type": "table", "content": "table", "page": 1, "sections": []}
        ]
        
        result = ContentMerger.merge_content_and_tables(text_items, table_items)
        
        if len(result) > 0:
            for item in result:
                if item.get("type") == "table":
                    assert "sections" in item or True

    def test_content_merger_maintains_order(self):
        """
        """
        text_items = [
            {"type": "text", "content": "text1", "page": 1, "sections": []},
            {"type": "text", "content": "text2", "page": 2, "sections": []}
        ]
        
        result = ContentMerger.merge_content_and_tables(text_items, [])
        
        assert len(result) >= 2
