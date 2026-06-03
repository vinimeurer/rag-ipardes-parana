"""
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.preprocessing.table_processor import TableProcessor, ProcessedTable


class TestProcessedTable:
    """
    """

    def test_processed_table_initialization(self):
        """
        """
        table = ProcessedTable(
            index=1,
            page=1,
            caption="Table 1",
            content="content",
            document="doc"
        )
        
        assert table.index == 1
        assert table.page == 1
        assert table.caption == "Table 1"

    def test_processed_table_without_caption(self):
        """
        """
        table = ProcessedTable(
            index=1,
            page=1,
            caption=None,
            content="content",
            document="doc"
        )
        
        assert table.caption is None


class TestTableProcessor:
    """
    """

    def test_table_processor_initialization(self):
        """
        """
        config = MagicMock()
        processor = TableProcessor(config)
        
        assert processor is not None

    def test_table_processor_load_tables_empty(self):
        """
        """
        config = MagicMock()
        processor = TableProcessor(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config.paths.extracted_dir = Path(tmpdir)
            
            result = processor.load_tables_for_document("nonexistent")
            
            assert isinstance(result, list)

    @patch('src.preprocessing.table_processor.Path.glob')
    def test_table_processor_find_table_files(self, mock_glob):
        """
        """
        mock_glob.return_value = []
        
        config = MagicMock()
        processor = TableProcessor(config)
        
        result = processor.load_tables_for_document("test_doc")
        
        assert isinstance(result, list)

    def test_table_processor_table_ordering(self):
        """
        """
        config = MagicMock()
        processor = TableProcessor(config)
        
        tables = [
            ProcessedTable(1, 2, "T1", "c", "d"),
            ProcessedTable(2, 1, "T2", "c", "d"),
            ProcessedTable(3, 3, "T3", "c", "d")
        ]
        
        assert len(tables) == 3
