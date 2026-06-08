import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from src.preprocessing.table_processor import TableProcessor, ProcessedTable
from src.core.preprocessing_config import TableProcessingConfig


class TestProcessedTable:

    def test_processed_table_initialization(self):

        table = ProcessedTable(
            table_index=1,
            page_number=1,
            caption="Table 1",
            content="content",
            document="doc"
        )

        assert table.caption == "Table 1"

    def test_processed_table_without_caption(self):

        table = ProcessedTable(
            table_index=1,
            page_number=1,
            caption=None,
            content="content",
            document="doc"
        )

        assert table.caption is None


class TestTableProcessor:

    def test_table_processor_initialization(self):

        processor = TableProcessor()
        assert processor is not None
        assert processor.cleaner is not None

    def test_load_tables_for_document_empty(self):

        processor = TableProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = processor.load_tables_for_document(
                "doc",
                Path(tmpdir)
            )

            assert result == []

    def test_load_tables_for_document_with_index(self):

        processor = TableProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            tables_dir = base / "doc" / "tables"
            tables_dir.mkdir(parents=True)

            index = {
                "tables": [
                    {
                        "table_index": 1,
                        "page_number": 1,
                        "caption": "Table A"
                    }
                ]
            }

            (tables_dir / "tables_index.json").write_text(
                json.dumps(index),
                encoding="utf-8"
            )

            (tables_dir / "table_001.md").write_text(
                "raw markdown content",
                encoding="utf-8"
            )

            result = processor.load_tables_for_document(
                "doc",
                base
            )

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["type"] == "table"

    def test_table_info_to_content_item_missing_file(self):

        processor = TableProcessor()

        result = processor._table_info_to_content_item(
            "doc",
            Path("/fake"),
            {"table_index": 1}
        )

        assert result is None

    def test_process_single_table_success(self):

        processor = TableProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            tables_dir = base / "doc" / "tables"
            tables_dir.mkdir(parents=True)

            config = TableProcessingConfig()
            processor.config = config

            file_path = tables_dir / config.markdown_file_pattern.format(1)
            file_path.write_text("table content", encoding="utf-8")

            table_info = {
                "table_index": 1,
                "page_number": 2,
                "caption": "Caption"
            }

            result = processor._process_single_table(
                "doc",
                tables_dir,
                table_info
            )

            assert result is not None
            assert result.table_index == 1
            assert result.document == "doc"

    def test_process_document_tables_and_save(self):

        processor = TableProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            extracted = base / "extracted"
            processed = base / "processed"

            tables_dir = extracted / "doc" / "tables"
            tables_dir.mkdir(parents=True)

            index = {
                "tables": [
                    {
                        "table_index": 1,
                        "page_number": 1,
                        "caption": "C1"
                    }
                ]
            }

            (tables_dir / "tables_index.json").write_text(
                json.dumps(index),
                encoding="utf-8"
            )

            config = TableProcessingConfig()
            processor.config = config

            file_path = tables_dir / config.markdown_file_pattern.format(1)
            file_path.write_text("content", encoding="utf-8")

            result = processor.process_document_tables(
                "doc",
                extracted,
                processed
            )

            assert len(result) == 1

            out_file = processed / "doc" / "tables" / config.json_output_pattern.format(1)
            assert out_file.exists()

    def test_save_processed_tables_empty(self):

        processor = TableProcessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            processor.save_processed_tables(
                "doc",
                [],
                Path(tmpdir),
                Path(tmpdir)
            )