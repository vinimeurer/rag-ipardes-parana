from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.pdf_splitter import split_pdf, cleanup_splits


class TestSplitPdf:

    def test_split_pdf_file_not_found(self):

        with pytest.raises(FileNotFoundError):
            split_pdf(Path("arquivo_inexistente.pdf"), 10)

    def test_split_pdf_invalid_batch_size_zero(self):

        with patch("src.ingestion.pdf_splitter.Path.exists", return_value=True):
            with pytest.raises(ValueError):
                split_pdf(Path("dummy.pdf"), 0)

    def test_split_pdf_invalid_batch_size_negative(self):

        with patch("src.ingestion.pdf_splitter.Path.exists", return_value=True):
            with pytest.raises(ValueError):
                split_pdf(Path("dummy.pdf"), -5)

    @patch("src.ingestion.pdf_splitter.PdfReader")
    def test_split_pdf_empty_pdf(self, mock_reader):

        reader = MagicMock()
        reader.pages = []

        mock_reader.return_value = reader

        with patch("src.ingestion.pdf_splitter.Path.exists", return_value=True):
            with pytest.raises(ValueError):
                split_pdf(Path("dummy.pdf"), 10)

    @patch("src.ingestion.pdf_splitter.open")
    @patch("src.ingestion.pdf_splitter.tempfile.NamedTemporaryFile")
    @patch("src.ingestion.pdf_splitter.PdfWriter")
    @patch("src.ingestion.pdf_splitter.PdfReader")
    def test_split_pdf_single_batch(
        self,
        mock_reader,
        mock_writer_class,
        mock_tempfile,
        mock_open,
    ):

        reader = MagicMock()
        reader.pages = [MagicMock(), MagicMock()]
        mock_reader.return_value = reader

        writer = MagicMock()
        mock_writer_class.return_value = writer

        temp = MagicMock()
        temp.name = "temp.pdf"
        mock_tempfile.return_value = temp

        with patch("src.ingestion.pdf_splitter.Path.exists", return_value=True):

            result = split_pdf(Path("dummy.pdf"), 10)

            assert len(result) == 1
            assert result[0][1] == 0

            assert writer.add_page.call_count == 2
            writer.write.assert_called_once()

    @patch("src.ingestion.pdf_splitter.open")
    @patch("src.ingestion.pdf_splitter.tempfile.NamedTemporaryFile")
    @patch("src.ingestion.pdf_splitter.PdfWriter")
    @patch("src.ingestion.pdf_splitter.PdfReader")
    def test_split_pdf_multiple_batches(
        self,
        mock_reader,
        mock_writer_class,
        mock_tempfile,
        mock_open,
    ):

        reader = MagicMock()
        reader.pages = [MagicMock() for _ in range(25)]
        mock_reader.return_value = reader

        writer = MagicMock()
        mock_writer_class.return_value = writer

        temp = MagicMock()
        temp.name = "temp.pdf"
        mock_tempfile.return_value = temp

        with patch("src.ingestion.pdf_splitter.Path.exists", return_value=True):

            result = split_pdf(Path("dummy.pdf"), 10)

            assert len(result) == 3

            offsets = [offset for _, offset in result]
            assert offsets == [0, 10, 20]

    @patch("src.ingestion.pdf_splitter.open")
    @patch("src.ingestion.pdf_splitter.tempfile.NamedTemporaryFile")
    @patch("src.ingestion.pdf_splitter.PdfWriter")
    @patch("src.ingestion.pdf_splitter.PdfReader")
    def test_split_pdf_exact_batch_boundary(
        self,
        mock_reader,
        mock_writer_class,
        mock_tempfile,
        mock_open,
    ):

        reader = MagicMock()
        reader.pages = [MagicMock() for _ in range(20)]
        mock_reader.return_value = reader

        writer = MagicMock()
        mock_writer_class.return_value = writer

        temp = MagicMock()
        temp.name = "temp.pdf"
        mock_tempfile.return_value = temp

        with patch("src.ingestion.pdf_splitter.Path.exists", return_value=True):

            result = split_pdf(Path("dummy.pdf"), 10)

            assert len(result) == 2


class TestCleanupSplits:

    def test_cleanup_splits_removes_files(self):

        file1 = MagicMock()
        file1.name = "file1.pdf"

        file2 = MagicMock()
        file2.name = "file2.pdf"

        cleanup_splits([
            (file1, 0),
            (file2, 10),
        ])

        file1.unlink.assert_called_once()
        file2.unlink.assert_called_once()

    def test_cleanup_splits_handles_exception(self):

        file1 = MagicMock()
        file1.name = "broken.pdf"
        file1.unlink.side_effect = OSError("erro")

        cleanup_splits([
            (file1, 0),
        ])

        file1.unlink.assert_called_once()

    def test_cleanup_splits_empty_list(self):

        cleanup_splits([])