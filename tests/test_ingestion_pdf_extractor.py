from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ingestion.pdf_extractor import (
    DoclingPDFExtractor,
    ExtractionResult,
    ExtractedPage,
)


class FakeProv:
    def __init__(self, page_no):
        self.page_no = page_no


class FakeItem:
    def __init__(self, text, page_no):
        self.text = text
        self.prov = [FakeProv(page_no)]


class FakeItemNoProv:
    def __init__(self, text):
        self.text = text
        self.prov = []


class FakeItemNoText:
    def __init__(self, page_no):
        self.text = ""
        self.prov = [FakeProv(page_no)]


class TestExtractionResult:

    def test_has_tables_true(self):

        result = ExtractionResult(
            pdf_key="doc",
            pdf_path=Path("doc.pdf"),
            tables=[MagicMock()]
        )

        assert result.has_tables is True

    def test_has_tables_false(self):

        result = ExtractionResult(
            pdf_key="doc",
            pdf_path=Path("doc.pdf"),
            tables=[]
        )

        assert result.has_tables is False


@patch.object(DoclingPDFExtractor, "_build_converter")
class TestDoclingPDFExtractor:

    def test_initialization(self, mock_build_converter):

        mock_build_converter.return_value = MagicMock()

        config = MagicMock()

        extractor = DoclingPDFExtractor(config)

        assert extractor.config == config
        assert extractor._converter is not None

    def test_extract_unknown_pdf_key(self, mock_build_converter):

        mock_build_converter.return_value = MagicMock()

        config = MagicMock()
        config.pdf_sources = {}

        extractor = DoclingPDFExtractor(config)

        result = extractor.extract("missing")

        assert result.success is False
        assert "não encontrada" in result.error

    def test_extract_file_not_found(self, mock_build_converter):

        mock_build_converter.return_value = MagicMock()

        source = MagicMock()
        source.local_path = Path("missing.pdf")

        config = MagicMock()
        config.pdf_sources = {"doc": source}

        extractor = DoclingPDFExtractor(config)

        result = extractor.extract("doc")

        assert result.success is False
        assert "Arquivo não encontrado" in result.error

    @patch("src.ingestion.pdf_extractor.cleanup_splits")
    @patch("src.ingestion.pdf_extractor.split_pdf")
    def test_extract_success(
        self,
        mock_split,
        mock_cleanup,
        mock_build_converter,
    ):

        mock_build_converter.return_value = MagicMock()

        mock_split.return_value = [
            (Path("batch_1.pdf"), 0)
        ]

        source = MagicMock()

        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        fake_path.name = "file.pdf"

        source.local_path = fake_path
        source.description = "Documento teste"

        config = MagicMock()
        config.pdf_sources = {"doc": source}
        config.batch_size = 50

        extractor = DoclingPDFExtractor(config)

        conversion = MagicMock()
        conversion.document = MagicMock()

        extractor._converter.convert.return_value = conversion

        extractor._extract_pages = MagicMock(
            return_value=[
                ExtractedPage(
                    page_number=1,
                    text="texto",
                    markdown="markdown"
                )
            ]
        )

        table_result = MagicMock()
        table_result.tables = []

        extractor._table_extractor = MagicMock()
        extractor._table_extractor.extract.return_value = table_result

        result = extractor.extract("doc")

        assert result.success is True
        assert len(result.pages) == 1
        assert result.metadata["total_pages"] == 1

        mock_cleanup.assert_called_once()

    @patch("src.ingestion.pdf_extractor.split_pdf")
    def test_extract_exception(
        self,
        mock_split,
        mock_build_converter,
    ):

        mock_build_converter.return_value = MagicMock()

        source = MagicMock()

        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        fake_path.name = "file.pdf"

        source.local_path = fake_path

        config = MagicMock()
        config.pdf_sources = {"doc": source}

        extractor = DoclingPDFExtractor(config)

        mock_split.side_effect = RuntimeError("erro teste")

        result = extractor.extract("doc")

        assert result.success is False
        assert "erro teste" in result.error


class TestExtractPages:

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_without_pages(self):

        extractor = MagicMock()

        doc = MagicMock()
        del doc.pages

        doc.export_to_text.return_value = "conteudo"

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 1
        assert result[0].page_number == 1

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_empty_pages(self):

        extractor = MagicMock()

        doc = MagicMock()
        doc.pages = {}
        doc.export_to_text.return_value = "conteudo"

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 1
        assert result[0].text == "conteudo"

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_regular_item(self):

        extractor = MagicMock()

        doc = MagicMock()
        doc.pages = {1: object()}

        doc.iterate_items.return_value = [
            (FakeItem("conteudo", 1), 0)
        ]

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 1
        assert "conteudo" in result[0].text

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_item_without_prov(self):

        extractor = MagicMock()

        doc = MagicMock()
        doc.pages = {1: object()}

        doc.iterate_items.return_value = [
            (FakeItemNoProv("conteudo"), 0)
        ]

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 1
        assert result[0].text == ""

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_item_without_text(self):

        extractor = MagicMock()

        doc = MagicMock()
        doc.pages = {1: object()}

        doc.iterate_items.return_value = [
            (FakeItemNoText(1), 0)
        ]

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 1

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_page_not_found(self):

        extractor = MagicMock()

        doc = MagicMock()
        doc.pages = {1: object()}

        doc.iterate_items.return_value = [
            (FakeItem("conteudo", 99), 0)
        ]

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 1
        assert result[0].text == ""

    @patch("docling_core.types.doc.TableItem", new=type("DummyTableItem", (), {}))
    def test_extract_pages_multiple_pages(self):

        extractor = MagicMock()

        doc = MagicMock()

        doc.pages = {
            1: object(),
            2: object(),
        }

        doc.iterate_items.return_value = [
            (FakeItem("pagina 1", 1), 0),
            (FakeItem("pagina 2", 2), 0),
        ]

        result = DoclingPDFExtractor._extract_pages(
            extractor,
            doc,
        )

        assert len(result) == 2

        assert result[0].page_number == 1
        assert result[1].page_number == 2