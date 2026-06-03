import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.preprocessing.preprocessor import Preprocessor
from src.core.preprocessing_config import PreprocessingConfig


@patch('src.preprocessing.preprocessor.TableProcessor')
@patch('src.preprocessing.preprocessor.get_processing_strategy')
@patch('src.preprocessing.preprocessor.ContentMerger')
@patch('src.preprocessing.preprocessor.ContentFilter')
@patch('src.preprocessing.preprocessor.PageParser')
class TestPreprocessor:
    """
    """

    def test_preprocessor_initialization(self, mock_parser, mock_filter, mock_merger, mock_processor, mock_table):
        config = PreprocessingConfig()
        preprocessor = Preprocessor(config)

        assert preprocessor.config == config

    def test_preprocessor_run_document(self, mock_parser, mock_filter, mock_merger, mock_processor, mock_table):

        mock_parser.parse_pages.return_value = [
            {
                "page_number": 1,
                "text": "# Content\nTest"
            }
        ]

        mock_table.return_value.load_tables_for_document.return_value = []

        mock_strategy = MagicMock()
        mock_strategy.process.return_value = [
            {"type": "text", "content": "abc"}
        ]
        mock_processor.return_value = mock_strategy

        mock_filter_instance = MagicMock()
        mock_filter_instance.filter.return_value = [
            {"type": "text", "content": "abc"}
        ]
        mock_filter.return_value = mock_filter_instance

        mock_merger.return_value.merge_content_and_tables.return_value = [
            {"type": "text", "content": "abc"}
        ]

        config = PreprocessingConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            config.paths.extracted_dir = Path(tmpdir)
            config.paths.processed_dir = Path(tmpdir)

            preprocessor = Preprocessor(config)

            doc_dir = Path(tmpdir) / "test"
            doc_dir.mkdir()

            extracted_file = doc_dir / "test.md"
            extracted_file.write_text("# Content\nTest")

            result = preprocessor.run_document("test")

            assert result is not None

    def test_preprocessor_run_all(self, mock_parser, mock_filter, mock_merger, mock_processor, mock_table):

        mock_parser.parse_pages.return_value = [
            {
                "page_number": 1,
                "text": "# Content\nTest"
            }
        ]

        mock_table.return_value.load_tables_for_document.return_value = []

        mock_strategy = MagicMock()
        mock_strategy.process.return_value = [
            {"type": "text", "content": "abc"}
        ]
        mock_processor.return_value = mock_strategy

        mock_filter_instance = MagicMock()
        mock_filter_instance.filter.return_value = [
            {"type": "text", "content": "abc"}
        ]
        mock_filter.return_value = mock_filter_instance

        config = PreprocessingConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            config.paths.extracted_dir = Path(tmpdir)
            config.paths.processed_dir = Path(tmpdir)

            preprocessor = Preprocessor(config)

            preprocessor.run_all()