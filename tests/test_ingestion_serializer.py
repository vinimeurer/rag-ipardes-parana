import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.ingestion.serializer import ExtractionSerializer


class TestExtractionSerializer:

    def test_serializer_initialization(self):

        config = MagicMock()

        serializer = ExtractionSerializer(config)

        assert serializer.config == config

    def test_save_text(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        with tempfile.TemporaryDirectory() as tmpdir:

            output_dir = Path(tmpdir)

            result = serializer._save_text(
                output_dir,
                "documento",
                "conteudo teste"
            )

            assert result.exists()
            assert result.read_text(encoding="utf-8") == "conteudo teste"

    def test_save_markdown(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        with tempfile.TemporaryDirectory() as tmpdir:

            output_dir = Path(tmpdir)

            result = serializer._save_markdown(
                output_dir,
                "documento",
                "# titulo"
            )

            assert result.exists()
            assert "# titulo" in result.read_text(encoding="utf-8")

    def test_save_json_without_tables(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        extraction = MagicMock()
        extraction.pdf_key = "doc"
        extraction.metadata = {"title": "teste"}
        extraction.pages = []
        extraction.tables = []
        extraction.has_tables = False

        with tempfile.TemporaryDirectory() as tmpdir:

            output_dir = Path(tmpdir)

            result = serializer._save_json(
                output_dir,
                extraction,
                "texto",
                "markdown"
            )

            assert result.exists()

            payload = json.loads(
                result.read_text(encoding="utf-8")
            )

            assert payload["tables_count"] == 0
            assert payload["tables_ref"] is None

    def test_save_json_with_tables(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        page = MagicMock()
        page.page_number = 1
        page.text = "conteudo"

        extraction = MagicMock()
        extraction.pdf_key = "doc"
        extraction.metadata = {}
        extraction.pages = [page]
        extraction.tables = [MagicMock()]
        extraction.has_tables = True

        with tempfile.TemporaryDirectory() as tmpdir:

            output_dir = Path(tmpdir)

            result = serializer._save_json(
                output_dir,
                extraction,
                "texto",
                "markdown"
            )

            payload = json.loads(
                result.read_text(encoding="utf-8")
            )

            assert payload["tables_count"] == 1
            assert payload["tables_ref"] == "tables/tables_index.json"

    def test_save_table_markdown(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        table = MagicMock()
        table.table_index = 1
        table.to_text_block.return_value = "|A|B|"

        with tempfile.TemporaryDirectory() as tmpdir:

            result = serializer._save_table_markdown(
                Path(tmpdir),
                table
            )

            assert result.exists()
            assert "|A|B|" in result.read_text(encoding="utf-8")

    def test_save_table_json(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        table = MagicMock()
        table.table_index = 1
        table.to_dict.return_value = {"a": 1}

        with tempfile.TemporaryDirectory() as tmpdir:

            result = serializer._save_table_json(
                Path(tmpdir),
                table
            )

            assert result.exists()

            payload = json.loads(
                result.read_text(encoding="utf-8")
            )

            assert payload["a"] == 1

    def test_save_tables(self):

        config = MagicMock()
        serializer = ExtractionSerializer(config)

        table = MagicMock()
        table.table_index = 1
        table.page_number = 2
        table.caption = "Tabela"
        table.num_rows = 10
        table.num_cols = 3

        table.to_text_block.return_value = "markdown"
        table.to_dict.return_value = {"id": 1}

        extraction = MagicMock()
        extraction.pdf_key = "doc"
        extraction.tables = [table]

        with tempfile.TemporaryDirectory() as tmpdir:

            result = serializer._save_tables(
                Path(tmpdir),
                extraction
            )

            assert "index" in result
            assert result["index"].exists()

            payload = json.loads(
                result["index"].read_text(encoding="utf-8")
            )

            assert payload["total_tables"] == 1

    def test_save_complete_without_tables(self):

        config = MagicMock()

        config.output.save_raw_text = True
        config.output.save_markdown = True
        config.output.save_json = True

        with tempfile.TemporaryDirectory() as tmpdir:

            output_dir = Path(tmpdir)

            config.pdf_output_dir.return_value = output_dir

            serializer = ExtractionSerializer(config)

            extraction = MagicMock()
            extraction.pdf_key = "doc"
            extraction.metadata = {}
            extraction.pages = []
            extraction.tables = []
            extraction.has_tables = False

            result = serializer.save(
                extraction,
                "texto",
                "markdown"
            )

            assert "text" in result
            assert "markdown" in result
            assert "json" in result

    def test_save_complete_with_tables(self):

        config = MagicMock()

        config.output.save_raw_text = True
        config.output.save_markdown = True
        config.output.save_json = True

        with tempfile.TemporaryDirectory() as tmpdir:

            output_dir = Path(tmpdir)

            config.pdf_output_dir.return_value = output_dir

            serializer = ExtractionSerializer(config)

            table = MagicMock()
            table.table_index = 1
            table.page_number = 1
            table.caption = "Tabela"
            table.num_rows = 2
            table.num_cols = 2

            table.to_text_block.return_value = "table"
            table.to_dict.return_value = {"table": 1}

            extraction = MagicMock()
            extraction.pdf_key = "doc"
            extraction.metadata = {}
            extraction.pages = []
            extraction.tables = [table]
            extraction.has_tables = True

            result = serializer.save(
                extraction,
                "texto",
                "markdown"
            )

            assert "tables_index" in result
            assert "tables_dir" in result

    def test_already_extracted_returns_false_when_overwrite_enabled(self):

        config = MagicMock()

        config.output.overwrite_existing = True

        serializer = ExtractionSerializer(config)

        assert serializer.already_extracted("doc") is False

    def test_already_extracted_existing_file(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            pdf_dir = Path(tmpdir)

            (pdf_dir / "doc.json").write_text("{}")

            config = MagicMock()
            config.output.overwrite_existing = False
            config.pdf_output_dir.return_value = pdf_dir

            serializer = ExtractionSerializer(config)

            assert serializer.already_extracted("doc") is True

    def test_already_extracted_missing_file(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            pdf_dir = Path(tmpdir)

            config = MagicMock()
            config.output.overwrite_existing = False
            config.pdf_output_dir.return_value = pdf_dir

            serializer = ExtractionSerializer(config)

            assert serializer.already_extracted("doc") is False